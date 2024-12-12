import discord
from discord.ext import commands
from collections import deque
from datetime import datetime

class DMTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store last 10 DMs using deque
        self.recent_dms = deque(maxlen=10)



    @commands.command(name='dmsall')
    @commands.has_permissions(administrator=True)  # Only administrators can use this command
    async def recent_dms(self, ctx):
        """Shows the most recent DMs received by the bot"""
        if not self.recent_dms:
            await ctx.send("No recent DMs to display.")
            return

        embed = discord.Embed(title="Recent DMs to Bot", color=discord.Color.blue())
        
        for dm in reversed(self.recent_dms):
            time_str = dm['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(
                name=f"{dm['author']} at {time_str}",
                value=f"Content: {dm['content'][:100]}..." if len(dm['content']) > 100 else f"Content: {dm['content']}",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DMTracker(bot))  # Changed from add_command to add_cog
