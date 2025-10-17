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
        self.heartbeat_url = "http://108.175.8.144:3005/api/heartbeat"
        self.heartbeat_enabled = True
        
        print("🚀 HeartbeatCog initialized, starting task...")
        self.heartbeat_task.start()
    
    @tasks.loop(seconds=30)
    async def heartbeat_task(self):
        try:
            if not self.heartbeat_enabled:
                return
            

            
            urls = ["http://108.175.8.144:3005/api/heartbeat"]
            
            ping = round(self.bot.latency * 1000) if self.bot.latency else None
            guild_count = len(self.bot.guilds)
            
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
            
            try:
                application = await self.bot.application_info()
                description = application.description or "A Discord bot for server management and utilities"
            except Exception:
                description = "A Discord bot for server management and utilities"
            
            bot_status = str(self.bot.status) if hasattr(self.bot, 'status') else 'unknown'
            
            activities = None
            current_activity = None
            
            if hasattr(self.bot, 'activity') and self.bot.activity is not None:
                activities = [{'name': self.bot.activity.name, 'type': self.bot.activity.type.value}]
                current_activity = {'name': self.bot.activity.name, 'type': self.bot.activity.type.value}
            elif hasattr(self.bot, 'user') and self.bot.user and hasattr(self.bot.user, 'activities') and self.bot.user.activities:
                user_activities = [{'name': act.name, 'type': act.type.value} for act in self.bot.user.activities if act.name]
                if user_activities:
                    activities = user_activities
                    current_activity = user_activities[0]
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
            
            success = False
            error_msg = None
            for url in urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                success = True
                                break
                            else:
                                error_msg = f"HTTP {response.status}"
                except Exception as e:
                    error_msg = str(e)
                    continue
            
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
            
            # Send Discord embed
            try:
                channel = self.bot.get_channel(1428618460946104351)
                if channel:
                    current_time = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    embed = discord.Embed(
                        title="💓 Heartbeat Status",
                        description=f"**Time:** {current_time}",
                        color=0x00ff00 if success else 0xff0000,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Status", value="✅ Success" if success else "❌ Failed", inline=True)
                    embed.add_field(name="Ping", value=f"{ping}ms" if ping else "N/A", inline=True)
                    embed.add_field(name="Uptime", value=uptime or "N/A", inline=True)
                    embed.add_field(name="Bot Status", value=bot_status, inline=True)
                    if not success and error_msg:
                        embed.add_field(name="Error", value=error_msg, inline=False)
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to send Discord heartbeat: {e}")
            
            # Write to log file
            try:
                with open('logs/heartbeat.log', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except:
                pass
                
        except Exception as e:
            print(f"💥 Heartbeat task error: {e}")
            
            # Send Discord notification about task failure
            try:
                channel = self.bot.get_channel(1428618460946104351)
                if channel:
                    embed = discord.Embed(
                        title="💥 Heartbeat Task Crashed",
                        color=0xff0000,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Error", value=str(e), inline=False)
                    embed.add_field(name="Status", value="Task will retry in 30 seconds", inline=False)
                    await channel.send(embed=embed)
            except Exception as discord_error:
                print(f"Failed to send Discord crash notification: {discord_error}")
            
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