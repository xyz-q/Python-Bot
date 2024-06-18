import discord
from discord.ext import commands
from colorama import Back, Fore, Style
import time
import json
import platform
from dotenv import load_dotenv
import os



# Define intents (adjust based on your bot's needs)
intents = discord.Intents.all()
# Initialize bot with intents
bot = commands.Bot(command_prefix=',', intents=intents)

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.'), intents=discord.Intents().all())

        self.cogslist = ["cogs.cog1"]

    async def setup_hook(self):
      for ext in self.cogslist:
        await self.load_extension(ext)

    async def on_ready(self):
        prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prfx + " Logged in as " + Fore.YELLOW + self.user.name)
        print(prfx + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('Pong!')


# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

client = Client()

client.run(DISCORD_TOKEN)

