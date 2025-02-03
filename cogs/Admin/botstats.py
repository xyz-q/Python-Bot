from discord.ext import commands
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
        self.start_time = self.load_or_create_start_time()
        
    def load_or_create_start_time(self):
        try:
            with open(self.uptime_file, 'r') as f:
                data = json.load(f)
                return data.get('start_time', time.time())
        except FileNotFoundError:
            # If file doesn't exist, create it with current time
            current_time = time.time()
            self.save_start_time(current_time)
            return current_time

    def save_start_time(self, start_time):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.uptime_file), exist_ok=True)
        
        with open(self.uptime_file, 'w') as f:
            json.dump({'start_time': start_time}, f)

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
        current_time = time.time()
        diff = current_time - self.start_time
        
        # Convert to datetime.timedelta for easier formatting
        uptime = timedelta(seconds=int(diff))
        
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60

        return f"{days}d {hours}h {minutes}m {seconds}s"


    @commands.command(name="resetuptime")
    @commands.is_owner()  # Only bot owner can use this command
    async def reset_uptime(self, ctx):
        """Resets the bot's uptime counter"""
        self.start_time = time.time()
        self.save_start_time(self.start_time)
        await ctx.send("Bot uptime has been reset!")

    @commands.command(name="botstats")
    async def show_stats(self, ctx):
        """Shows bot statistics including uptime and command usage"""
        uptime = self.format_uptime()
        total_commands, command_breakdown = self.calculate_total_commands()

        embed = discord.Embed(
            title="Bot Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        # Add uptime field
        embed.add_field(
            name="Uptime",
            value=uptime,
            inline=False
        )

        # Add start time field
        start_datetime = datetime.fromtimestamp(self.start_time)
        embed.add_field(
            name="Started On",
            value=start_datetime.strftime("%Y-%m-%d %H:%M:%S UTC"),
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

    @commands.command(name="commandstats")
    async def command_stats(self, ctx, command_name: str = None):
        """Shows statistics for a specific command or lists all commands"""
        stats = self.load_command_stats()
        total_commands, command_breakdown = self.calculate_total_commands()

        if command_name:
            # Show stats for specific command
            command_total = command_breakdown.get(command_name.lower(), 0)
            embed = discord.Embed(
                title=f"Command Statistics: {command_name}",
                description=f"Total uses: {command_total}",
                color=discord.Color.blue()
            )
        else:
            # Show all commands
            embed = discord.Embed(
                title="All Command Statistics",
                color=discord.Color.blue()
            )
            
            # Sort commands by usage
            sorted_commands = sorted(command_breakdown.items(), key=lambda x: x[1], reverse=True)
            
            # Split into chunks of 15 for multiple fields if needed
            for i in range(0, len(sorted_commands), 15):
                chunk = sorted_commands[i:i+15]
                field_value = "\n".join(f"`{cmd}`: {count}" for cmd, count in chunk)
                embed.add_field(
                    name=f"Commands {i+1}-{i+len(chunk)}",
                    value=field_value,
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))
