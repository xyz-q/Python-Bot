import discord
from discord.ext import commands
import time
from datetime import datetime, timedelta

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Shows how long the bot has been running."""
        current_time = datetime.utcnow()
        uptime_delta = current_time - self.start_time
        
        # Convert timedelta to days, hours, minutes, seconds
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Create a nice formatted message
        uptime_str = f"I've been running for: "
        if days > 0:
            uptime_str += f"{days} days, "
        if hours > 0:
            uptime_str += f"{hours} hours, "
        if minutes > 0:
            uptime_str += f"{minutes} minutes, "
        uptime_str += f"{seconds} seconds"

        # Create and send an embed
        embed = discord.Embed(
            title="🕒 Bot Uptime",
            description=uptime_str,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Uptime(bot))
