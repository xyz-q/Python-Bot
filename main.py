from colorama import Back, Fore, Style
import platform
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import glob
import asyncio
import time  # Add this line
from discord import app_commands, Interaction, Object
from discord.ui import Button, View



load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
intents.message_content = True
intents.dm_messages = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix=',', owner_id=110927272210354176, intents=intents)


 
class Client(commands.Bot):
    def __init__(self):
        super().__init__(help_command=None, command_prefix=commands.when_mentioned_or(','), owner_id=110927272210354176, intents=discord.Intents().all())
        self.cogslist = self.get_all_cogs("cogs")

    def get_all_cogs(self, directory):
        pattern = os.path.join(directory, "**", "*.py")
        return [f.replace("/", ".").replace("\\", ".")[:-3] for f in glob.glob(pattern, recursive=True)]

    async def setup_hook(self):
        print("\n=== Loading Cogs ===\n")
        for ext in self.cogslist:
            try:
                await self.load_extension(ext)
                print(f"{Fore.GREEN}✓ {ext}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}✗ {ext}: {str(e)}{Style.RESET_ALL}")
        print("\n")
        print("=== All Cogs Loaded ===\n")


    async def on_ready(self):
        if not hasattr(self, 'start_time'):
            self.start_time = discord.utils.utcnow()
            
        prfx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prfx + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))

    async def on_message(self, message):
        if message.author.bot:
            return  
    

    
    


        if message.author.id == 110927272210354176:
            return

                   
                                                                        
       
        blacklist_cog = self.bot.get_cog('Blacklist')    
        if blacklist_cog and message.author.id in blacklist_cog.blacklisted_users:

            if message.content.startswith(","):
                
                return
            return   
        
        await self.process_commands(message)

client = Client()
async def main():
    async with client:
        await client.start(DISCORD_TOKEN)

asyncio.run(main())



