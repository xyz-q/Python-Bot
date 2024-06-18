import discord
from discord.ext import commands
import os
import json

AFK_FILE = 'afk_data.json'

def load_afk_data():
    if os.path.exists(AFK_FILE):
        with open(AFK_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_afk_data(data):
    with open(AFK_FILE, 'w') as file:
        json.dump(data, file, indent=4)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = load_afk_data()

    @commands.command()
    async def afk(self, ctx, *, reason=""):
        user_id = str(ctx.author.id)

        if user_id in self.afk_users:
            # Remove AFK status
            self.afk_users.pop(user_id)
            save_afk_data(self.afk_users)
            await ctx.send(f"{ctx.author.mention} is no longer AFK.")
        else:
            # Set AFK status
            self.afk_users[user_id] = reason
            save_afk_data(self.afk_users)
            await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {reason}")

def setup(bot):
    bot.add_cog(AFK(bot))
