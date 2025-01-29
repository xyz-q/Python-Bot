import discord
from discord.ext import commands
from datetime import datetime
import json
import os

class FirstSeen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.first_seen = {}
        self.data_file = ".json/first_seen.json"
        self._load_data()

    def _load_data(self):
        """Load first-seen data from JSON file if it exists"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                # Convert string keys back to integers and strings to datetime
                self.first_seen = {
                    int(user_id): datetime.fromisoformat(timestamp)
                    for user_id, timestamp in data.items()
                }

    def _save_data(self):
        """Save first-seen data to JSON file"""
        with open(self.data_file, 'w') as f:
            # Convert datetime objects to ISO format strings
            data = {
                str(user_id): timestamp.isoformat()
                for user_id, timestamp in self.first_seen.items()
            }
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Record first time a user uses any command"""
        if not ctx.author.bot:  # Ignore bot commands
            user_id = ctx.author.id
            if user_id not in self.first_seen:
                self.first_seen[user_id] = datetime.now()
                self._save_data()

    def get_first_seen(self, user_id: int) -> datetime:
        """Get when a user was first seen using the bot"""
        return self.first_seen.get(user_id)

    def get_user_count(self) -> int:
        """Get total number of users who have used the bot"""
        return len(self.first_seen)

    @commands.command()
    async def firstseen(self, ctx, member: discord.Member = None):
        """Show when a user first used the bot"""
        target_user = member or ctx.author
        timestamp = self.get_first_seen(target_user.id)

        if timestamp:
            embed = discord.Embed(
                title="First Bot Interaction",
                color=target_user.color
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Add first seen date
            embed.add_field(
                name="First Seen",
                value=f"<t:{int(timestamp.timestamp())}:F>",
                inline=False
            )
            
            # Add relative time
            embed.add_field(
                name="Time Since",
                value=f"<t:{int(timestamp.timestamp())}:R>",
                inline=False
            )

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{target_user.name} hasn't used any bot commands yet!")

async def setup(bot):
    await bot.add_cog(FirstSeen(bot))