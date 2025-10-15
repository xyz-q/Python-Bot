import discord
from discord.ext import commands, tasks
import psutil
import platform
from datetime import datetime
import aiohttp
import json
import asyncio
import time
import subprocess

class WebStatsReporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_url = "https://zxpq.ca/api/server-stats"  # Your VPS endpoint
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_check_time = datetime.now()
        self.report_stats.start()

    def cog_unload(self):
        self.report_stats.cancel()

    @tasks.loop(minutes=2)  # Send stats every 2 minutes
    async def report_stats(self):
        try:
            stats = await self.collect_stats()
            await self.send_to_vps(stats)
        except Exception as e:
            print(f"Error reporting stats: {e}")

    @report_stats.before_loop
    async def before_report_stats(self):
        await self.bot.wait_until_ready()

    async def collect_stats(self):
        # Calculate network and disk speeds
        current_net_io = psutil.net_io_counters()
        current_disk_io = psutil.disk_io_counters()
        current_time = datetime.now()
        time_delta = (current_time - self.last_check_time).total_seconds()
        
        upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta / 1024  # KB/s
        download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta / 1024  # KB/s
        
        read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta / (1024 * 1024)  # MB/s
        write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta / (1024 * 1024)  # MB/s
        
        self.last_net_io = current_net_io
        self.last_disk_io = current_disk_io
        self.last_check_time = current_time

        # Collect system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime_seconds = psutil.boot_time()
        current_uptime = datetime.now().timestamp() - uptime_seconds
        
        # Ping VPS for network latency
        vps_latency = await self.ping_vps()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": platform.node(),
            "uptime_seconds": int(current_uptime),
            "cpu": {
                "usage_percent": cpu_percent,
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "usage_percent": memory.percent,
                "used_gb": round(memory.used / (1024 ** 3), 2),
                "total_gb": round(memory.total / (1024 ** 3))
            },
            "disk": {
                "usage_percent": disk.percent,
                "used_gb": round(disk.used / (1024 ** 3), 0),
                "total_gb": round(disk.total / (1024 ** 3), 0),
                "read_speed_mb": round(read_speed, 2),
                "write_speed_mb": round(write_speed, 2)
            },
            "network": {
                "upload_speed_kb": round(upload_speed, 2),
                "download_speed_kb": round(download_speed, 2),
                "total_sent_mb": round(current_net_io.bytes_sent / (1024**2), 2),
                "total_recv_mb": round(current_net_io.bytes_recv / (1024**2), 2)
            },
            "bot": {
                "discord_latency_ms": round(self.bot.latency * 1000),
                "vps_latency_ms": vps_latency,
                "guilds": len(self.bot.guilds),
                "users": len(self.bot.users)
            }
        }

    async def ping_vps(self):
        """Ping Google DNS to measure network latency"""
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # Parse ping output for latency
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'time=' in line:
                        latency_str = line.split('time=')[1].split(' ms')[0]
                        return round(float(latency_str))
            return 999
        except:
            return 999  # Return high latency if ping fails
    
    async def send_to_vps(self, stats):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.vps_url, json=stats, timeout=10) as response:
                    if response.status != 200:
                        print(f"Failed to send stats: {response.status}")
        except Exception as e:
            print(f"Error sending stats to VPS: {e}")

    @commands.command()
    async def teststats(self, ctx):
        """Test stats collection and display"""
        stats = await self.collect_stats()
        
        # Send detailed stats to Discord
        embed = discord.Embed(title="📊 Detailed Server Stats Debug", color=0x00ff00)
        embed.add_field(name="🖥️ CPU", value=f"{stats['cpu']['usage_percent']}%", inline=True)
        embed.add_field(name="💾 Memory", value=f"{stats['memory']['used_gb']}/{stats['memory']['total_gb']} GB\n({stats['memory']['usage_percent']}%)", inline=True)
        embed.add_field(name="💿 Disk", value=f"{stats['disk']['used_gb']}/{stats['disk']['total_gb']} GB\n({stats['disk']['usage_percent']}%)", inline=True)
        embed.add_field(name="🤖 VPS Latency", value=f"{stats['bot']['vps_latency_ms']}ms", inline=True)
        embed.add_field(name="🏠 Hostname", value=stats['hostname'], inline=True)
        embed.add_field(name="⏰ Timestamp", value=stats['timestamp'], inline=True)
        
        await ctx.send(embed=embed)
        
        # Also send to VPS for testing
        try:
            await self.send_to_vps(stats)
            await ctx.send("✅ Stats also sent to VPS successfully!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send to VPS: {e}")

async def setup(bot):
    await bot.add_cog(WebStatsReporter(bot))