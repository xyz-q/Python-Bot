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
            uptime_seconds = int((discord.utils.utcnow() - self.bot.start_time).total_seconds())
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            
            if days > 0:
                uptime = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                uptime = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                uptime = f"{minutes}m {seconds}s"
            else:
                uptime = f"{seconds}s"
        else:
            uptime = None
            
        # Get bot application info
        try:
            application = await self.bot.application_info()
            description = application.description or "A Discord bot for server management and utilities"
            print(f"[HEARTBEAT] Application description: {description}")
        except Exception as e:
            description = "A Discord bot for server management and utilities"
            print(f"[HEARTBEAT] Failed to get application info: {e}")
        
        # Get bot status (online, idle, dnd, offline)
        bot_status = str(self.bot.status) if hasattr(self.bot, 'status') else 'unknown'
        print(f"[HEARTBEAT] Bot status: {bot_status}")
        
        # Get activities
        activities = None
        current_activity = None
        print(f"[HEARTBEAT] Bot activity: {self.bot.activity}")
        print(f"[HEARTBEAT] Bot activities: {getattr(self.bot, 'activities', 'No activities attribute')}")
        
        if hasattr(self.bot, 'activity') and self.bot.activity:
            activities = [{'name': self.bot.activity.name, 'type': self.bot.activity.type.value}]
            current_activity = {'name': self.bot.activity.name, 'type': self.bot.activity.type.value}
            print(f"[HEARTBEAT] Found activity: {current_activity}")
        elif hasattr(self.bot, 'activities') and self.bot.activities:
            activities = [{'name': act.name, 'type': act.type.value} for act in self.bot.activities]
            if self.bot.activities:
                current_activity = {'name': self.bot.activities[0].name, 'type': self.bot.activities[0].type.value}
            print(f"[HEARTBEAT] Found activities: {activities}")
        else:
            print(f"[HEARTBEAT] No activity found")
        
        payload = {
            'ping': ping,
            'guildCount': guild_count,
            'uptime': uptime,
            'description': description,
            'activities': activities,
            'currentActivity': current_activity,
            'status': bot_status
        }
        
        print(f"[HEARTBEAT] Sending payload: {payload}")
        
        success = False
        for url in urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            success = True
                            print(f"[HEARTBEAT] Successfully sent to {url}")
                            break
                        else:
                            print(f"[HEARTBEAT] Failed to send to {url}, status: {response.status}")
            except Exception as e:
                print(f"[HEARTBEAT] Error sending to {url}: {e}")
                continue
        

    
    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        self.heartbeat_task.cancel()

async def setup(bot):
    await bot.add_cog(HeartbeatCog(bot))