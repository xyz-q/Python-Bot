from discord.ext import commands, tasks
import time
import json
import discord
from datetime import datetime, timedelta
import os

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.uptime_file = ".json/uptime_stats.json"
        self.command_stats_file = ".json/command_stats.json"
        self.load_uptime_stats()
        self.update_runtime.start()  # Start the background task
        
    def load_uptime_stats(self):
        try:
            with open(self.uptime_file, 'r') as f:
                data = json.load(f)
                self.total_seconds = data.get('total_seconds', 0)
                self.total_minutes = data.get('total_minutes', 0)
                self.total_hours = data.get('total_hours', 0)
                self.total_days = data.get('total_days', 0)
        except FileNotFoundError:
            self.total_seconds = 0
            self.total_minutes = 0
            self.total_hours = 0
            self.total_days = 0
            self.save_uptime_stats()

    def save_uptime_stats(self):
        os.makedirs(os.path.dirname(self.uptime_file), exist_ok=True)
        with open(self.uptime_file, 'w') as f:
            json.dump({
                'total_seconds': self.total_seconds,
                'total_minutes': self.total_minutes,
                'total_hours': self.total_hours,
                'total_days': self.total_days
            }, f, indent=4)

    @tasks.loop(seconds=17.0)
    async def update_runtime(self):
        """Update the runtime every 17 seconds"""
        self.total_seconds += 17

        # Update minutes if we have 60 or more seconds
        while self.total_seconds >= 60:
            self.total_seconds -= 60
            self.total_minutes += 1

        # Update hours if we have 60 or more minutes
        while self.total_minutes >= 60:
            self.total_minutes -= 60
            self.total_hours += 1

        # Update days if we have 24 or more hours
        while self.total_hours >= 24:
            self.total_hours -= 24
            self.total_days += 1

        # Save the updated stats
        self.save_uptime_stats()

    def load_command_stats(self):
        try:
            with open(self.command_stats_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def calculate_total_commands(self):
        stats = self.load_command_stats()
        total_commands = 0
        command_breakdown = {}

        # Calculate totals for each command across all users
        for user_id, commands in stats.items():
            for command, count in commands.items():
                total_commands += count
                command_breakdown[command] = command_breakdown.get(command, 0) + count

        return total_commands, command_breakdown

    def format_uptime(self):
        return f"{self.total_days}d {self.total_hours}h {self.total_minutes}m {self.total_seconds}s"

    @commands.command(name="botstats")
    async def show_stats(self, ctx):
        """Shows bot statistics including uptime and command usage"""
        uptime = self.format_uptime()
        total_commands, command_breakdown = self.calculate_total_commands()

        embed = discord.Embed(
            title="Bot Statistics",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        # Add total uptime field
        embed.add_field(
            name="Total Running Time",
            value=uptime,
            inline=False
        )

        # Add total commands field
        embed.add_field(
            name="Total Commands Used",
            value=str(total_commands),
            inline=False
        )

        # Add top 10 most used commands
        sorted_commands = sorted(command_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]
        top_commands = "\n".join(f"`{cmd}`: {count}" for cmd, count in sorted_commands)
        
        embed.add_field(
            name="Top 10 Commands",
            value=top_commands or "No commands used yet",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="resetuptime")
    @commands.is_owner()
    async def reset_uptime(self, ctx):
        """Resets the bot's uptime counter"""
        self.total_seconds = 0
        self.total_minutes = 0
        self.total_hours = 0
        self.total_days = 0
        self.save_uptime_stats()
        await ctx.send("Bot uptime has been reset!")

    def cog_unload(self):
        """Called when the cog is unloaded"""
        self.update_runtime.cancel()  # Stop the background task
        self.save_uptime_stats()

    @update_runtime.before_loop
    async def before_update_runtime(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Statistics(bot))
