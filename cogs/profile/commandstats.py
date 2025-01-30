import discord
from discord.ext import commands
from collections import defaultdict
import json
import os

class CommandStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats = defaultdict(lambda: defaultdict(int))
        self.stats_file = ".json/command_stats.json"
        self._load_stats()

    def _load_stats(self):
        """Load stats from JSON file if it exists"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                # Convert string keys back to integers for user IDs
                data = json.load(f)
                self.stats = defaultdict(lambda: defaultdict(int))
                for user_id, commands in data.items():
                    self.stats[int(user_id)] = defaultdict(int, commands)

    def _save_stats(self):
        """Save stats to JSON file"""
        with open(self.stats_file, 'w') as f:
            # Convert defaultdict to regular dict for JSON serialization
            json.dump({str(k): dict(v) for k, v in self.stats.items()}, f, indent=4)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Increment command usage when a command is successfully used"""
        user_id = ctx.author.id
        command_name = ctx.command.qualified_name
        self.stats[user_id][command_name] += 1
        self._save_stats()

    def get_user_stats(self, user_id: int) -> dict:
        """Get command stats for a specific user"""
        return dict(self.stats[user_id])

    def get_total_commands(self, user_id: int) -> int:
        """Get total number of commands used by a user"""
        return sum(self.stats[user_id].values())

    def get_favorite_command(self, user_id: int) -> tuple:
        """Get user's most used command and its count"""
        user_stats = self.stats[user_id]
        if not user_stats:
            return None, 0
        favorite_cmd = max(user_stats.items(), key=lambda x: x[1])
        return favorite_cmd

    def format_number(self, number: int) -> str:
        """Format number to K/M/B format"""
        if number >= 10_000_000_000:  # 10 Billion and above
            return f"{number/1_000_000_000:.2f}B"
        elif number >= 1_000_000:    # Millions (including 1-9.9B)
            return f"{int(number/1_000_000)}M"
        elif number >= 1_000:        # Thousands
            return f"{number/1_000:.1f}K"
        return str(number)

    @commands.command()
    async def mystats(self, ctx):
        """Display command usage stats for the user"""
        user_stats = self.get_user_stats(ctx.author.id)
        if not user_stats:
            await ctx.send("You haven't used any commands yet!")
            return

        embed = discord.Embed(title=f"Command Stats for {ctx.author.name}",
                            color=discord.Color.gold())
        
        # Add total commands used
        total_commands = self.get_total_commands(ctx.author.id)
        embed.add_field(name="Total Commands Used", value=str(total_commands), inline=False)
        
        # Add individual command stats
        command_stats = "\n".join(f"`{cmd}`: {count}" for cmd, count in user_stats.items())
        embed.add_field(name="Command Usage", value=command_stats or "No commands used", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandStats(bot))
