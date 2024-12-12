import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class BanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ban", description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="The member to ban",
        reason="The reason for the ban",
        delete_messages="Number of days worth of messages to delete (0-7)"
    )
    async def ban(
        self, 
        ctx: commands.Context, 
        member: discord.Member, 
        reason: Optional[str] = "No reason provided",
        delete_messages: Optional[int] = 0
    ):
        # Check if the bot can ban members
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("I don't have permission to ban members!")
            return

        # Check if the target member is higher in role hierarchy
        if ctx.author.top_role <= member.top_role:
            await ctx.send("You cannot ban this member as their role is higher than or equal to yours!")
            return

        # Check if the bot's role is higher than the target member
        if ctx.guild.me.top_role <= member.top_role:
            await ctx.send("I cannot ban this member as their role is higher than mine!")
            return

        # Ensure delete_messages is within valid range (0-7 days)
        delete_messages = max(0, min(7, delete_messages))

        try:
            # Send a DM to the user being banned
            try:
                await member.send(f"You have been banned from {ctx.guild.name}\nReason: {reason}")
            except discord.HTTPException:
                # If DM fails, continue with the ban
                pass

            # Ban the member
            await member.ban(reason=reason, delete_message_days=delete_messages)
            
            # Create and send an embed with ban information
            embed = discord.Embed(
                title="Member Banned",
                color=discord.Color.red()
            )
            embed.add_field(name="Banned User", value=f"{member.name}#{member.discriminator}", inline=False)
            embed.add_field(name="Banned By", value=f"{ctx.author.name}#{ctx.author.discriminator}", inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this member!")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while banning the member: {str(e)}")

    @ban.error
    async def ban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to ban members!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Member not found!")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Please mention a valid member.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(BanSystem(bot))
