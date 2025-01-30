import discord
from discord.ext import commands
import json

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_file = ".json/blacklist.json"
        # Load existing blacklist or create empty one
        try:
            with open(self.blacklist_file, "r") as f:
                self.blacklisted_users = json.load(f)
        except FileNotFoundError:
            self.blacklisted_users = []
            self._save_blacklist()

    def _save_blacklist(self):
        with open(self.blacklist_file, "w") as f:
            json.dump(self.blacklisted_users, f)

    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.User = None):
        """
        Toggle blacklist for a user or show the blacklist
        Usage: !blacklist [user]
        """
        if user is None:
            # Show the blacklist
            embed = discord.Embed(title="Blacklisted Users", color=discord.Color.gold())
            
            if self.blacklisted_users:
                users_list = []
                for user_id in self.blacklisted_users:
                    user = self.bot.get_user(user_id)
                    users_list.append(f"• {user.name if user else user_id}")
                embed.description = "\n".join(users_list)
            else:
                embed.description = "No users are blacklisted"
            
            await ctx.send(embed=embed)
            return

        # Toggle the user's blacklist status
        if user.id in self.blacklisted_users:
            self.blacklisted_users.remove(user.id)
            await ctx.send(f"✅ **{user.name}** has been removed from the blacklist.")
        else:
            self.blacklisted_users.append(user.id)
            await ctx.send(f"⛔ **{user.name}** has been added to the blacklist.")
        
        self._save_blacklist()



async def setup(bot):
    await bot.add_cog(Blacklist(bot))
