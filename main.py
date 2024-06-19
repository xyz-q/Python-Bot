from colorama import Back, Fore, Style
import time
import platform
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import glob

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=',', intents=intents)

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(','), intents=discord.Intents().all())
        self.cogslist = self.get_all_cogs("cogs")

    def get_all_cogs(self, directory):
        """Recursively gets all cogs from a directory."""
        pattern = os.path.join(directory, "**", "*.py")
        return [f.replace("/", ".").replace("\\", ".")[:-3] for f in glob.glob(pattern, recursive=True)]

    async def setup_hook(self):
        for ext in self.cogslist:
            try:
                await self.load_extension(ext)
                print(f"Loaded extension: {ext}")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

    async def on_ready(self):
        prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prfx + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))
        synced = await self.tree.sync()
        print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")

if __name__ == "__main__":
    client = Client()
    client.run(DISCORD_TOKEN)
