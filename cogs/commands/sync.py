import discord
from discord.ext import commands
from colorama import Back, Fore, Style
import time

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tree = bot.tree 

    @commands.command(name='sync', description='Sync slash commands.')
    async def sync_slash_commands(self, ctx):
        await ctx.send("Syncing slash commands...")
        try:
            prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
            synced = await self.tree.sync()
            print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")
            await ctx.send("Slash commands synchronized successfully!")
            print("Slash commands synchronized successfully!")
        except Exception as e:
            await ctx.send(f"Failed to sync slash commands: {e}")
            print(f"Failed to sync slash commands: {e}")

async def setup(bot):
    await bot.add_cog(Sync(bot))


