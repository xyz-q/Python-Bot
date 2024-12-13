import discord
from discord.ext import commands
from datetime import timedelta

class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason=None):
        """Timeout a member for a specified duration (in minutes)"""
        try:
            # Convert duration to timedelta
            time = timedelta(minutes=duration)
            
            # Create DM embed
            dm_embed = discord.Embed(
                title="You've Been Timed Out",
                description=f"You have been timed out in {ctx.guild.name}, please create a ticket in the server using /ticket if you would like to appeal.",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Duration", value=f"{duration} minutes", inline=False)
            dm_embed.add_field(name="Moderator", value=ctx.author.name, inline=False)
            if reason:
                dm_embed.add_field(name="Reason", value=reason, inline=False)
            
            # Try to send DM to user
            try:
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("Could not send DM to the user.")
            
            # Apply timeout
            await member.timeout(time, reason=reason)
            
            # Send confirmation message in channel
            channel_embed = discord.Embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out for {duration} minutes.",
                color=discord.Color.orange()
            )
            if reason:
                channel_embed.add_field(name="Reason", value=reason)
            channel_embed.add_field(name="Moderator", value=ctx.author.mention)
            
            await ctx.send(embed=channel_embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout this member.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason=None):
        """Remove timeout from a member"""
        try:
            # Create DM embed for untimeout
            dm_embed = discord.Embed(
                title="Your Timeout Has Been Removed",
                description=f"Your timeout in {ctx.guild.name} has been removed",
                color=discord.Color.green()
            )
            dm_embed.add_field(name="Moderator", value=ctx.author.name, inline=False)
            if reason:
                dm_embed.add_field(name="Reason", value=reason, inline=False)
            
            # Try to send DM to user
            try:
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("Could not send DM to the user.")
            
            # Remove timeout
            await member.timeout(None, reason=reason)
            
            # Send confirmation message in channel
            channel_embed = discord.Embed(
                title="Timeout Removed",
                description=f"Timeout has been removed from {member.mention}",
                color=discord.Color.green()
            )
            if reason:
                channel_embed.add_field(name="Reason", value=reason)
            channel_embed.add_field(name="Moderator", value=ctx.author.mention)
            
            await ctx.send(embed=channel_embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to remove timeout from this member.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @timeout.error
    async def timeout_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to timeout members.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Member not found.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a member and duration (in minutes).")

async def setup(bot):
    await bot.add_cog(Timeout(bot))
