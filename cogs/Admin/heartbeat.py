import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import os
from datetime import datetime
import pytz

HEARTBEAT_FILE = ".json/heartbeat_message.json"

class HeartbeatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.heartbeat_url = "http://108.175.8.144:3005/api/heartbeat"
        self.heartbeat_enabled = True
        self.history = []  # rolling list of bools, max 20
        self.message_id = None
        self.channel_id = 1428618460946104351
        self._load_message_id()
        self.heartbeat_task.start()
        self.channel_cleanup.start()

    def _load_message_id(self):
        try:
            with open(HEARTBEAT_FILE, 'r') as f:
                self.message_id = json.load(f).get("message_id")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_message_id(self):
        os.makedirs(".json", exist_ok=True)
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump({"message_id": self.message_id}, f)

    def _build_embed(self, success, ping, uptime, bot_status, error_msg=None):
        self.history.append(success)
        if len(self.history) > 20:
            self.history.pop(0)

        graph = " ".join("✅" if h else "❌" for h in self.history)

        utc_time = discord.utils.utcnow()
        local_time = utc_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/Denver'))
        current_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        embed = discord.Embed(
            title="💓 Heartbeat Status",
            color=0x00ff00 if success else 0xff0000,
            timestamp=utc_time
        )
        embed.add_field(name="Last 20 Pings", value=graph or "No data yet", inline=False)
        embed.add_field(name="Status", value="✅ Success" if success else "❌ Failed", inline=True)
        embed.add_field(name="Ping", value=f"{ping}ms" if ping else "N/A", inline=True)
        embed.add_field(name="Uptime", value=uptime or "N/A", inline=True)
        embed.add_field(name="Bot Status", value=bot_status, inline=True)
        if not success and error_msg:
            embed.add_field(name="Error", value=error_msg, inline=False)
        embed.set_footer(text=f"Last updated: {current_time}")
        return embed

    async def _update_message(self, embed):
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return

            if self.message_id:
                try:
                    msg = await channel.fetch_message(self.message_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound:
                    pass

            msg = await channel.send(embed=embed)
            self.message_id = msg.id
            self._save_message_id()
        except Exception as e:
            print(f"\033[91mError updating heartbeat message: {e}\033[0m")

    @tasks.loop(seconds=15)
    async def heartbeat_task(self):
        try:
            if not self.heartbeat_enabled:
                return

            ping = round(self.bot.latency * 1000) if self.bot.latency and self.bot.latency != float('inf') else None
            guild_count = len(self.bot.guilds)

            if hasattr(self.bot, 'start_time'):
                uptime_seconds = int((discord.utils.utcnow() - self.bot.start_time).total_seconds())
                days, rem = divmod(uptime_seconds, 86400)
                hours, rem = divmod(rem, 3600)
                minutes, seconds = divmod(rem, 60)
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
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.heartbeat_url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            success = True
                        else:
                            error_msg = f"HTTP {response.status}"
            except Exception as e:
                error_msg = str(e)

            embed = self._build_embed(success, ping, uptime, bot_status, error_msg)
            await self._update_message(embed)

            try:
                with open('logs/heartbeat.log', 'a') as f:
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
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass

        except Exception as e:
            print(f"💥 Heartbeat task error: {e}")

    @tasks.loop(minutes=5)
    async def channel_cleanup(self):
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel or not self.message_id:
                return
            async for msg in channel.history(limit=100):
                if msg.id != self.message_id:
                    try:
                        await msg.delete()
                        await asyncio.sleep(0.5)
                    except (discord.Forbidden, discord.NotFound):
                        pass
        except Exception as e:
            print(f"\033[91mError in heartbeat channel cleanup: {e}\033[0m")

    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)

    @channel_cleanup.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.is_owner()
    async def stophb(self, ctx):
        self.heartbeat_enabled = False
        await ctx.send("❌ Heartbeat stopped")

    @commands.command()
    @commands.is_owner()
    async def starthb(self, ctx):
        self.heartbeat_enabled = True
        await ctx.send("✅ Heartbeat started")

    def cog_unload(self):
        self.heartbeat_task.cancel()
        self.channel_cleanup.cancel()

async def setup(bot):
    await bot.add_cog(HeartbeatCog(bot))
