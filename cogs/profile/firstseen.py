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
                self.first_seen = {
                    int(user_id): datetime.fromisoformat(timestamp)
                    for user_id, timestamp in data.items()
                }

    def _save_data(self):
        """Save first-seen data to JSON file"""
        with open(self.data_file, 'w') as f:
            data = {
                str(user_id): timestamp.isoformat()
                for user_id, timestamp in self.first_seen.items()
            }
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Record first time a user uses any command"""
        if not ctx.author.bot:
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
            
            embed.add_field(
                name="First Seen",
                value=f"<t:{int(timestamp.timestamp())}:F>",
                inline=False
            )
            
            embed.add_field(
                name="Time Since",
                value=f"<t:{int(timestamp.timestamp())}:R>",
                inline=False
            )

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{target_user.name} hasn't used any bot commands yet!")

    @commands.command()
    @commands.is_owner()
    async def setfirstseen(self, ctx, member: discord.Member, *, date_str: str):
        """Set a user's first seen date manually (Admin only)
        Format: YYYY-MM-DD HH:MM:SS
        Example: !setfirstseen @User 2023-01-01 12:00:00"""
        try:
            new_date = datetime.fromisoformat(date_str)
            
            self.first_seen[member.id] = new_date
            self._save_data()
            
            embed = discord.Embed(
                title="First Seen Date Updated",
                color=member.color,
                description=f"Updated first seen date for {member.mention}"
            )
            embed.add_field(
                name="New First Seen Date",
                value=f"<t:{int(new_date.timestamp())}:F>",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("Invalid date format! Please use: YYYY-MM-DD HH:MM:SS")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @setfirstseen.error
    async def setfirstseen_error(self, ctx, error):
        """Error handler for setfirstseen command"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command! (Administrator required)")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide both a user and a date! Format: !setfirstseen @User YYYY-MM-DD HH:MM:SS")


async def setup(bot):
    await bot.add_cog(FirstSeen(bot))