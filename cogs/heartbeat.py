import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import os
from colorama import Fore, Style

class HeartbeatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Get server URL from environment variable, fallback to localhost
        server_host = os.getenv('HEARTBEAT_SERVER', 'localhost')
        server_port = os.getenv('HEARTBEAT_PORT', '3001')
        self.heartbeat_url = f"http://{server_host}:{server_port}/api/heartbeat"
        print(f"{Fore.CYAN}🔗 Heartbeat URL: {self.heartbeat_url}{Style.RESET_ALL}")
        self.heartbeat_task.start()
    
    @tasks.loop(seconds=30)  # Send heartbeat every 30 seconds
    async def heartbeat_task(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.heartbeat_url) as response:
                    if response.status == 200:
                        print(f"{Fore.GREEN}✓ Heartbeat sent successfully{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠ Heartbeat failed: {response.status}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Heartbeat error: {e}{Style.RESET_ALL}")
    
    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()
        print(f"{Fore.CYAN}🔄 Starting heartbeat system...{Style.RESET_ALL}")
    
    def cog_unload(self):
        self.heartbeat_task.cancel()
        print(f"{Fore.YELLOW}⚠ Heartbeat system stopped{Style.RESET_ALL}")

async def setup(bot):
    await bot.add_cog(HeartbeatCog(bot))
    print(f"{Fore.GREEN}✓ Heartbeat cog loaded{Style.RESET_ALL}")