import discord
from discord.ext import commands
import json
import os

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_file = ".json/blacklist.json"
        self.blacklisted_users = self._load_blacklist()

    def _load_blacklist(self):
        """Load the blacklist from file with error handling"""
        try:
            os.makedirs(os.path.dirname(self.blacklist_file), exist_ok=True)
            
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, "r") as f:
                    data = json.load(f)

                return data
            else:
                print("No blacklist file found, creating new one")
                self._save_blacklist([])
                return []
        except Exception as e:
            print(f"Error loading blacklist: {e}")
            return []

    def _save_blacklist(self, blacklist=None):
        """Save the blacklist to file with error handling"""
        if blacklist is None:
            blacklist = self.blacklisted_users
            
        try:
            os.makedirs(os.path.dirname(self.blacklist_file), exist_ok=True)
            
            with open(self.blacklist_file, "w") as f:
                json.dump(blacklist, f, indent=4)
            print(f"Saved blacklist: {blacklist}")
            return True
        except Exception as e:
            print(f"Error saving blacklist: {e}")
            return False

    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.User = None):
        if user is None:
            embed = discord.Embed(title="Blacklisted Users", color=discord.Color.red())
            if self.blacklisted_users:
                users_list = []
                for user_id in self.blacklisted_users:
                    user = self.bot.get_user(int(user_id))
                    users_list.append(f"• {user.name if user else user_id}")
                embed.description = "\n".join(users_list)
            else:
                embed.description = "No users are blacklisted"
            await ctx.send(embed=embed)
            return

        user_id = int(user.id)
        
        print(f"Current blacklist before change: {self.blacklisted_users}")
        print(f"Attempting to modify blacklist for user: {user_id}")

        if user_id in self.blacklisted_users:
            self.blacklisted_users.remove(user_id)
            success = self._save_blacklist()
            if success:
                await ctx.send(f"<:add:1328511998647861390> **{user.name}** has been removed from the blacklist.")
            else:
                await ctx.send("<:remove:1328511957208268800> Failed to save blacklist changes.")
        else:
            self.blacklisted_users.append(user_id)
            success = self._save_blacklist()
            if success:
                await ctx.send(f"⛔ **{user.name}** has been added to the blacklist.")
            else:
                await ctx.send("<:remove:1328511957208268800> Failed to save blacklist changes.")

        print(f"Current blacklist after change: {self.blacklisted_users}")

        self.blacklisted_users = self._load_blacklist()
        print(f"Reloaded blacklist: {self.blacklisted_users}")



async def setup(bot):
    await bot.add_cog(Blacklist(bot))
