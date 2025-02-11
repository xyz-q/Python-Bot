import discord
from discord.ext import commands, tasks
import psutil
import platform
from datetime import datetime



class SystemMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitor_loop.start()
        
    def cog_unload(self):
        self.monitor_loop.cancel()

    @tasks.loop(seconds=10)  # Update every 10 seconds
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
                self.monitor_message = await channel.send(embed=embed(self))
            else:
                try:
                    # Try to edit the existing message
                    await self.monitor_message.edit(embed=embed(self))
                except discord.NotFound:
                    # If the message was deleted, send a new one
                    self.monitor_message = await channel.send(embed=embed(self))

    @monitor_loop.before_loop
    async def before_monitor_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(1338669385082208296)
        if channel:
            # Clear all messages in the channel
            await channel.purge()
            # Create new monitor message
            embed = await self.get_system_stats()
            self.monitor_message = await channel.send(embed=embed(self))

    async def get_system_stats(self):
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
        disk_used = f"{disk.used / (1024 ** 3):.2f} GB"
        disk_total = f"{disk.total / (1024 ** 3):.2f} GB"

        embed = discord.Embed(
            title="System Monitor",
            description=f"System stats for {platform.node()}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="CPU",
            value=f"Usage: {cpu_percent}%\nFrequency: {cpu_freq:.2f} MHz",
            inline=False
        )
        embed.add_field(
            name="Memory",
            value=f"Usage: {memory_percent}%\nUsed: {memory_used}/{memory_total}",
            inline=False
        )
        embed.add_field(
            name="Disk",
            value=f"Usage: {disk_percent}%\nUsed: {disk_used}/{disk_total}",
            inline=False
        )

        return embed

    @commands.command()
    async def sysinfo(self, ctx):
        """Get current system information"""
        embed = await self.get_system_stats()
        await ctx.send(embed=embed(self))

async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))
