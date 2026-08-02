import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional


class KickSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(
        member="The member to kick",
        reason="The reason for the kick"
    )
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "No reason provided"):
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("I don't have permission to kick members!")
            return

        if ctx.author.top_role <= member.top_role:
            await ctx.send("You cannot kick this member as their role is higher than or equal to yours!")
            return

        if ctx.guild.me.top_role <= member.top_role:
            await ctx.send("I cannot kick this member as their role is higher than mine!")
            return

        try:
            try:
                await member.send(f"You have been kicked from {ctx.guild.name}\nReason: {reason}")
            except discord.HTTPException:
                pass

            await member.kick(reason=reason)

            embed = discord.Embed(title="Member Kicked", color=discord.Color.orange())
            embed.add_field(name="Kicked User", value=member.name, inline=False)
            embed.add_field(name="Kicked By", value=ctx.author.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this member!")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while kicking the member: {str(e)}")

    @kick.error
    async def kick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to kick members!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Member not found!")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Please mention a valid member.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")


async def setup(bot):
    await bot.add_cog(KickSystem(bot))
