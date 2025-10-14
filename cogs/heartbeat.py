import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import os
from colorama import Fore, Style

class HeartbeatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Gaming PC IP address
        self.heartbeat_url = "http://192.168.0.115:3001/api/heartbeat"
        print(f"{Fore.CYAN}🔗 Heartbeat URL: {self.heartbeat_url}{Style.RESET_ALL}")
        self.heartbeat_task.start()
    
    @tasks.loop(seconds=30)  # Send heartbeat every 30 seconds
    async def heartbeat_task(self):
        # Try both possible server locations
        urls = [
            "http://192.168.0.115:3001/api/heartbeat",  # Gaming PC
            "http://192.168.0.158:3001/api/heartbeat",  # Server PC
            "http://localhost:3001/api/heartbeat"        # Same machine
        ]
        
        # Gather bot stats
        ping = round(self.bot.latency * 1000) if self.bot.latency else None
        guild_count = len(self.bot.guilds)
        
        # Calculate uptime
        if hasattr(self.bot, 'start_time'):
            uptime_seconds = (discord.utils.utcnow() - self.bot.start_time).total_seconds()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            if days > 0:
                uptime = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                uptime = f"{hours}h {minutes}m"
            else:
                uptime = f"{minutes}m"
        else:
            uptime = None
            
        # Get activities
        activities = None
        if hasattr(self.bot, 'activity') and self.bot.activity:
            activities = [{'name': self.bot.activity.name, 'type': self.bot.activity.type.value}]
        elif hasattr(self.bot, 'activities') and self.bot.activities:
            activities = [{'name': act.name, 'type': act.type.value} for act in self.bot.activities]
        
        payload = {
            'ping': ping,
            'guildCount': guild_count,
            'uptime': uptime,
            'activities': activities
        }
        
        success = False
        for url in urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print(f"{Fore.GREEN}✓ Heartbeat sent to {url.split('//')[1]} (Ping: {ping}ms, Guilds: {guild_count}){Style.RESET_ALL}")
                            success = True
                            break
            except Exception:
                continue
        
        if not success:
            print(f"{Fore.RED}✗ All heartbeat endpoints failed{Style.RESET_ALL}")
    
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