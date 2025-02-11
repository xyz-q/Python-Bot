import discord
from discord.ext import commands, tasks
import psutil
import platform
from datetime import datetime

class MonitorButtons(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)  # Buttons will deactivate after 60 seconds
        self.cog = cog

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self.cog.get_system_stats()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Detailed CPU", style=discord.ButtonStyle.blurple, emoji="💻")
    async def cpu_detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get detailed CPU information
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        
        embed = discord.Embed(
            title="Detailed CPU Information",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="CPU Cores",
            value=f"Physical cores: {psutil.cpu_count(logical=False)}\n"
                  f"Total cores: {cpu_count}",
            inline=False
        )
        
        # Add individual core usage
        core_info = ""
        for i, percentage in enumerate(cpu_percent):
            core_info += f"Core {i}: {percentage}%\n"
        embed.add_field(name="Core Usage", value=core_info, inline=False)
        
        embed.add_field(
            name="CPU Frequency",
            value=f"Current: {cpu_freq.current:.2f}MHz\n"
                  f"Min: {cpu_freq.min:.2f}MHz\n"
                  f"Max: {cpu_freq.max:.2f}MHz",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Detailed Memory", style=discord.ButtonStyle.blurple, emoji="🧮")
    async def memory_detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get detailed memory information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        embed = discord.Embed(
            title="Detailed Memory Information",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="RAM",
            value=f"Total: {memory.total / (1024**3):.2f} GB\n"
                  f"Available: {memory.available / (1024**3):.2f} GB\n"
                  f"Used: {memory.used / (1024**3):.2f} GB\n"
                  f"Percentage: {memory.percent}%",
            inline=False
        )
        
        embed.add_field(
            name="Swap",
            value=f"Total: {swap.total / (1024**3):.2f} GB\n"
                  f"Used: {swap.used / (1024**3):.2f} GB\n"
                  f"Free: {swap.free / (1024**3):.2f} GB\n"
                  f"Percentage: {swap.percent}%",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji="✖️")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

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
                self.monitor_message = await channel.send(embed=embed, view=MonitorButtons(self))
            else:
                try:
                    # Try to edit the existing message
                    await self.monitor_message.edit(embed=embed, view=MonitorButtons(self))
                except discord.NotFound:
                    # If the message was deleted, send a new one
                    self.monitor_message = await channel.send(embed=embed, view=MonitorButtons(self))

    @monitor_loop.before_loop
    async def before_monitor_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(1338669385082208296)
        if channel:
            # Clear all messages in the channel
            await channel.purge()
            # Create new monitor message
            embed = await self.get_system_stats()
            self.monitor_message = await channel.send(embed=embed, view=MonitorButtons(self))

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
        await ctx.send(embed=embed, view=MonitorButtons(self))

async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))
