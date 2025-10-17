import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import os
from colorama import Fore, Style
import time
import json
from datetime import datetime

class HeartbeatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Gaming PC IP address
        self.heartbeat_url = "http://108.175.8.144:3005/api/heartbeat"
        self.heartbeat_enabled = True

        self.heartbeat_task.start()
    
    @tasks.loop(seconds=30)  # Send heartbeat every 30 seconds
    async def heartbeat_task(self):
        try:
            if not self.heartbeat_enabled:
                return
            
            print(f"Sending heartbeat at {datetime.now()}...")
        # VPS server only
        urls = [
            "http://108.175.8.144:3005/api/heartbeat"   # VPS server (Bot status server)
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
        except Exception:
            description = "A Discord bot for server management and utilities"
        
        # Get bot status (online, idle, dnd, offline)
        bot_status = str(self.bot.status) if hasattr(self.bot, 'status') else 'unknown'
        
        # Get activities - check both activity and user presence
        activities = None
        current_activity = None
        
        # Check bot.activity first
        if hasattr(self.bot, 'activity') and self.bot.activity is not None:
            activities = [{'name': self.bot.activity.name, 'type': self.bot.activity.type.value}]
            current_activity = {'name': self.bot.activity.name, 'type': self.bot.activity.type.value}
        # Check user activities if bot.activity is None
        elif hasattr(self.bot, 'user') and self.bot.user and hasattr(self.bot.user, 'activities') and self.bot.user.activities:
            user_activities = [{'name': act.name, 'type': act.type.value} for act in self.bot.user.activities if act.name]
            if user_activities:
                activities = user_activities
                current_activity = user_activities[0]
        # Check if bot has activities attribute
        elif hasattr(self.bot, 'activities') and self.bot.activities:
            activities = [{'name': act.name, 'type': act.type.value} for act in self.bot.activities if act.name]
            if activities:
                current_activity = activities[0]
        
        payload = {
            'ping': ping,
            'guildCount': guild_count,
            'uptime': uptime,
            'description': description,
            'activities': activities,
            'currentActivity': current_activity,
            'status': bot_status
        }
        
        # Send heartbeat to servers
        success = False
        error_msg = None
        for url in urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print(f"✅ Heartbeat sent successfully to {url}")
                            success = True
                            break
                        else:
                            error_msg = f"HTTP {response.status}"
                            print(f"❌ Heartbeat failed: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Heartbeat error: {error_msg}")
                continue
        
        # Log heartbeat result
        if success:
            print(f"💚 Heartbeat successful - Ping: {ping}ms, Guilds: {guild_count}")
        else:
            print(f"💔 Heartbeat failed - Error: {error_msg}")
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'ping': ping,
            'guilds': guild_count,
            'uptime': uptime,
            'status': bot_status
        }
        if not success:
            log_entry['error'] = error_msg
        
            # Write to log file
            try:
                with open('logs/heartbeat.log', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                print(f"Failed to write heartbeat log: {e}")
        except Exception as e:
            print(f"Heartbeat task error: {e}")
            # Log the error
            try:
                with open('logs/heartbeat.log', 'a') as f:
                    error_log = {
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': f"Task error: {str(e)}"
                    }
                    f.write(json.dumps(error_log) + '\n')
            except:
                pass
        

    
    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()
        # Wait a bit more to ensure status is set
        await asyncio.sleep(2)
    
    @commands.command()
    @commands.is_owner()
    async def stophb(self, ctx):
        """Stop heartbeat to simulate bot offline"""
        self.heartbeat_enabled = False
        await ctx.send("❌ Heartbeat stopped - bot will appear offline on website")
    
    @commands.command()
    @commands.is_owner()
    async def starthb(self, ctx):
        """Start heartbeat again"""
        self.heartbeat_enabled = True
        await ctx.send("✅ Heartbeat started - bot will appear online on website")
    
    def cog_unload(self):
        self.heartbeat_task.cancel()

async def setup(bot):
    await bot.add_cog(HeartbeatCog(bot))