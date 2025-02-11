import discord
from discord.ext import commands, tasks
import psutil
import platform
from datetime import datetime
import subprocess
import platform


class SystemMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize these variables
        self.monitor_message = None
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = datetime.now()
        # Start the loop
        self.monitor_loop.start()
        
    def cog_unload(self):
        self.monitor_loop.cancel()

    @tasks.loop(seconds=25)  # Update every 10 seconds
    async def monitor_loop(self):
        channel = self.bot.get_channel(1338669385082208296)
        if channel:
            # Delete any messages that aren't our monitor message
            async for message in channel.history(limit=None):
                if message != self.monitor_message:
                    await message.delete()

            embed = await self.get_system_stats()
            
            if self.monitor_message is None:
                # If no message exists, send a new one
                self.monitor_message = await channel.send(embed=embed, view=None)
            else:
                try:
                    # Try to edit the existing message
                    await self.monitor_message.edit(embed=embed, view=None)
                except discord.NotFound:
                    # If the message was deleted, send a new one
                    self.monitor_message = await channel.send(embed=embed, view=None)

    @monitor_loop.before_loop
    async def before_monitor_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(1338669385082208296)
        if channel:
            # Clear all messages in the channel
            await channel.purge()
            # Create new monitor message
            embed = await self.get_system_stats()
            self.monitor_message = await channel.send(embed=embed, view=None)

    async def get_system_stats(self):

        # Calculate network speed
        current_net_io = psutil.net_io_counters()
        current_time = datetime.now()
        time_delta = (current_time - self.last_check_time).total_seconds()
        
        upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta / 1024  # KB/s
        download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta / 1024  # KB/s
        
        self.last_net_io = current_net_io
        self.last_check_time = current_time

        # Bot latency (ping)
        latency = round(self.bot.latency * 1000)  # Convert to ms
        api_latency = round(self.bot.latency * 1000)

        # Network usage (add with other psutil calls)
        network = psutil.net_io_counters()
        bytes_sent = f"{network.bytes_sent / (1024**2):.2f}"
        bytes_recv = f"{network.bytes_recv / (1024**2):.2f}"

        # Temperature (some systems might not support this)
        try:
            if platform.system() == "Linux":
                sensors_output = subprocess.check_output(['sensors']).decode()
                temp_info = []
                
                for line in sensors_output.split('\n'):
                    if ':' in line and '°C' in line:
                        # Only include lines with actual temperature readings
                        if 'N/A' not in line:
                            # Split at first colon to get sensor name and value
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                name = parts[0].strip()
                                # Extract the actual temperature value
                                temp = parts[1].split('(')[0].strip()
                                if '+' in temp or '-' in temp:  # Make sure we have a temperature value
                                    temp_info.append(f"{name}: {temp}")
                
                temp_text = '\n'.join(temp_info) if temp_info else "No temperature readings found"
            else:
                temp_text = f"N/A ({platform.system()})"
        except Exception as e:
            temp_text = f"Temperature monitoring unavailable: {str(e)}"



        
        # CPU Info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq().current
        
        # Memory Info
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = f"{memory.used / (1024 ** 3):.2f} GB"
        memory_total = f"{memory.total / (1024 ** 3):.2f} GB"

        # Disk Info
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = f"{disk.used / (1024 ** 3):.0f} GB"
        disk_total = f"{disk.total / (1024 ** 3):.0f} GB"

        embed = discord.Embed(
            title="System Monitor",
            description=f"System stats for {platform.node()}",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="CPU",
            value=f"Usage: {cpu_percent}%\nFrequency: {cpu_freq:.2f} MHz\n{temp_text}",
            inline=True
        )
        embed.add_field(
            name="Network Speed",
            value=f"Upload: {upload_speed:.2f} KB/s\n"
                  f"Download: {download_speed:.2f} KB/s\n"
                  f"Total Up: {bytes_sent} MB\n"
                  f"Total Down: {bytes_recv} MB\n"
                  f"Latecny: {latency}ms",
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(
            name="Memory",
            value=f"Usage: {memory_percent}%\nUsed: {memory_used}/{memory_total}",
            inline=True
        )
        
        embed.add_field(
            name="Disk",
            value=f"Usage: {disk_percent}%\n{disk_used}/{disk_total}",
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)



        return embed

    @commands.command()
    async def sysinfo(self, ctx):
        """Get current system information"""
        embed = await self.get_system_stats()
        await ctx.send(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))
