import discord
from discord.ext import commands, tasks
import psutil
import platform
import asyncio
import subprocess
from datetime import datetime, timedelta

MONITOR_CHANNEL_ID = 1338669385082208296


def status_color(*percents):
    worst = max(percents)
    if worst >= 85:
        return discord.Color.red()
    if worst >= 60:
        return discord.Color.orange()
    return discord.Color.green()


SKIP_FS_TYPES = {"squashfs", "tmpfs", "devtmpfs", "overlay", "iso9660"}


def get_cpu_temp(temps):
    package_vals = []
    core_vals = []
    all_vals = []

    for chip, entries in temps.items():
        for entry in entries:
            label = (entry.label or chip or "").lower()
            all_vals.append(entry.current)
            if "package" in label:
                package_vals.append(entry.current)
            elif "core" in label:
                core_vals.append(entry.current)

    if package_vals:
        return sum(package_vals) / len(package_vals)
    if core_vals:
        return sum(core_vals) / len(core_vals)
    if all_vals:
        return sum(all_vals) / len(all_vals)
    return None


def get_disk_partitions():
    partitions = []
    seen_mounts = set()
    for part in psutil.disk_partitions(all=False):
        if part.fstype.lower() in SKIP_FS_TYPES:
            continue
        if part.mountpoint in seen_mounts:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        if usage.total < 1024 ** 3:
            continue
        seen_mounts.add(part.mountpoint)
        partitions.append((part.mountpoint, usage))
    return partitions


def format_uptime(seconds):
    delta = timedelta(seconds=int(seconds))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


class SystemMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitor_message = None

        now = datetime.now()
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = now
        self.last_disk_io = psutil.disk_io_counters()
        self.last_disk_time = now

        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != MONITOR_CHANNEL_ID:
            return
        if message.author.id == self.bot.user.id:
            return
        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    @tasks.loop(seconds=120)
    async def monitor_loop(self):
        channel = self.bot.get_channel(MONITOR_CHANNEL_ID)
        if not channel:
            return

        embed = await self.get_system_stats()

        if self.monitor_message is None:
            self.monitor_message = await channel.send(embed=embed)
        else:
            try:
                await self.monitor_message.edit(embed=embed)
            except discord.NotFound:
                self.monitor_message = await channel.send(embed=embed)

    @monitor_loop.before_loop
    async def before_monitor_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(MONITOR_CHANNEL_ID)
        if channel:
            await channel.purge()
            embed = await self.get_system_stats()
            self.monitor_message = await channel.send(embed=embed)

    def _blocking_stats(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()

        temps = {}
        try:
            temps = psutil.sensors_temperatures()
        except (AttributeError, Exception):
            temps = {}

        if not temps:
            try:
                sensors_output = subprocess.check_output(["sensors"], timeout=3).decode()
                parsed = {}
                for line in sensors_output.split("\n"):
                    if ":" in line and "\u00b0C" in line and "N/A" not in line:
                        name, rest = line.split(":", 1)
                        value = rest.split("(")[0].strip()
                        if value:
                            parsed.setdefault("sensors", []).append((name.strip(), value))
                temps = {"sensors_cli": [type("T", (), {"label": n, "current": v}) for n, v in parsed.get("sensors", [])]} if parsed else {}
            except Exception:
                temps = {}

        load_avg = None
        try:
            load_avg = psutil.getloadavg()
        except (AttributeError, OSError):
            load_avg = None

        return cpu_percent, cpu_freq, temps, load_avg

    async def get_system_stats(self):
        cpu_percent, cpu_freq, temps, load_avg = await asyncio.to_thread(self._blocking_stats)

        now = datetime.now()

        net_time_delta = max((now - self.last_net_time).total_seconds(), 0.001)
        current_net_io = psutil.net_io_counters()
        upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / net_time_delta / 1024
        download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / net_time_delta / 1024
        bytes_sent = current_net_io.bytes_sent / (1024 ** 2)
        bytes_recv = current_net_io.bytes_recv / (1024 ** 2)
        self.last_net_io = current_net_io
        self.last_net_time = now

        disk_time_delta = max((now - self.last_disk_time).total_seconds(), 0.001)
        current_disk_io = psutil.disk_io_counters()
        read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / disk_time_delta / (1024 * 1024)
        write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / disk_time_delta / (1024 * 1024)
        self.last_disk_io = current_disk_io
        self.last_disk_time = now

        latency = round(self.bot.latency * 1000)

        memory = psutil.virtual_memory()
        disk_partitions = get_disk_partitions()
        worst_disk_percent = max((usage.percent for _, usage in disk_partitions), default=0)

        uptime_seconds = now.timestamp() - psutil.boot_time()

        embed = discord.Embed(
            title="System Monitor",
            description=f"{platform.node()}  •  Uptime: {format_uptime(uptime_seconds)}",
            color=status_color(cpu_percent, memory.percent, worst_disk_percent),
            timestamp=now,
        )
        embed.set_footer(text="Last updated")

        cpu_lines = [
            f"Usage: {cpu_percent:.1f}%",
            f"Freq: {cpu_freq.current:.0f} MHz" if cpu_freq else "Freq: N/A",
        ]
        if load_avg:
            cpu_lines.append(f"Load: {load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}")

        cpu_temp = get_cpu_temp(temps)
        cpu_lines.append(f"Temp: {cpu_temp:.1f}\u00b0C" if cpu_temp is not None else "Temp: not available")

        embed.add_field(name="CPU", value="\n".join(cpu_lines), inline=True)

        mem_lines = [
            f"Usage: {memory.percent:.1f}%",
            f"{memory.used / (1024 ** 3):.2f} / {memory.total / (1024 ** 3):.2f} GB",
        ]
        swap = psutil.swap_memory()
        if swap.total:
            mem_lines.append(f"Swap: {swap.percent:.1f}% ({swap.used / (1024 ** 3):.2f}/{swap.total / (1024 ** 3):.2f} GB)")
        embed.add_field(name="Memory", value="\n".join(mem_lines), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        disk_lines = [f"Read: {read_speed:.2f} MB/s  Write: {write_speed:.2f} MB/s", ""]
        for i, (mountpoint, usage) in enumerate(disk_partitions[:6], start=1):
            disk_lines.append(
                f"Disk {i}: {usage.percent:.1f}% ({usage.used / (1024 ** 3):.0f}/{usage.total / (1024 ** 3):.0f} GB)"
            )
        if not disk_partitions:
            disk_lines.append("No partitions found")
        embed.add_field(name="Disk", value="\n".join(disk_lines), inline=True)

        net_lines = [
            f"Latency: {latency} ms",
            f"Down: {download_speed:.2f} KB/s",
            f"Up: {upload_speed:.2f} KB/s",
            f"Total Down: {bytes_recv:.2f} MB",
            f"Total Up: {bytes_sent:.2f} MB",
        ]
        embed.add_field(name="Network", value="\n".join(net_lines), inline=True)

        return embed

    @commands.command()
    async def sysinfo(self, ctx):
        embed = await self.get_system_stats()
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SystemMonitor(bot))