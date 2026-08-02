import discord
from discord.ext import commands, tasks
import os
import json
import gzip
import shutil
import asyncio
import io
from datetime import datetime, timedelta
from pathlib import Path

STATUS_FILE = ".json/logstatus_message.json"
MAX_FILE_SIZE = 128 * 1024 * 1024  # 128MB
MAX_DAYS = 30


class LogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_channel_id = 1337674275427061871
        self.status_message_id = None
        self._load_status_message_id()

        self.log_dir = Path('logs')
        self.archive_dir = self.log_dir / 'archived'
        self.log_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)

        self.cleanup_old_logs.start()
        self.auto_status.start()
        self.channel_cleanup.start()

    def _load_status_message_id(self):
        try:
            with open(STATUS_FILE, 'r') as f:
                self.status_message_id = json.load(f).get("message_id")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_status_message_id(self):
        os.makedirs(".json", exist_ok=True)
        with open(STATUS_FILE, 'w') as f:
            json.dump({"message_id": self.status_message_id}, f)

    def cog_unload(self):
        self.cleanup_old_logs.cancel()
        self.auto_status.cancel()
        self.channel_cleanup.cancel()

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}" if unit != 'B' else f"{size_bytes} B"
            size_bytes /= 1024

    async def log_to_file(self, log_entry: str):
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f"discord_log_{current_date}.txt"

        # Size-based rotation
        if log_file.exists() and log_file.stat().st_size >= MAX_FILE_SIZE:
            await self.rotate_log(log_file)

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    async def rotate_log(self, log_file: Path):
        try:
            if not log_file.exists() or log_file.stat().st_size <= 10:
                if log_file.exists():
                    log_file.unlink()
                return

            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            archive_name = self.archive_dir / f"{log_file.stem}_{timestamp}.gz"

            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_name, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            if archive_name.exists() and archive_name.stat().st_size > 0:
                log_file.unlink()
                print(f"Archived {log_file.name} -> {archive_name.name}")
            else:
                log_file.unlink()
        except Exception as e:
            print(f"Error rotating {log_file}: {e}")
            try:
                log_file.unlink()
            except:
                pass

    async def get_status_embed(self):
        logs_current_size = 0
        logs_archive_size = 0
        num_files = 0
        num_archives = 0
        oldest_date = None
        today_size = 0
        today_str = datetime.now().strftime('%Y-%m-%d')

        for log_file in self.log_dir.glob('discord_log_*.txt'):
            size = log_file.stat().st_size
            logs_current_size += size
            num_files += 1
            if today_str in log_file.name:
                today_size = size
            try:
                date_str = log_file.stem.split('discord_log_')[1][:10]
                d = datetime.strptime(date_str, '%Y-%m-%d')
                if oldest_date is None or d < oldest_date:
                    oldest_date = d
            except (ValueError, IndexError):
                pass

        for archive in self.archive_dir.glob('*.gz'):
            logs_archive_size += archive.stat().st_size
            num_archives += 1
            try:
                date_str = archive.stem.split('discord_log_')[1][:10]
                d = datetime.strptime(date_str, '%Y-%m-%d')
                if oldest_date is None or d < oldest_date:
                    oldest_date = d
            except (ValueError, IndexError):
                pass

        next_cleanup = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')
        oldest_str = oldest_date.strftime('%Y-%m-%d') if oldest_date else 'N/A'

        embed = discord.Embed(title="Log Status", color=discord.Color.gold(), timestamp=datetime.now())

        embed.add_field(
            name="Log Files",
            value=f"Current: `{num_files}`\nArchived: `{num_archives}`\nOldest: `{oldest_str}`",
            inline=True
        )
        embed.add_field(
            name="Storage",
            value=f"Today: `{self.format_size(today_size)}`\nCurrent: `{self.format_size(logs_current_size)}`\nArchives: `{self.format_size(logs_archive_size)}`",
            inline=True
        )
        embed.add_field(
            name="Settings",
            value=f"Retention: `{MAX_DAYS} days`\nRotation: `{self.format_size(MAX_FILE_SIZE)}`\nNext cleanup: `{next_cleanup}`",
            inline=True
        )
        embed.set_footer(text="Last Updated")
        return embed

    async def _update_status_message(self):
        try:
            channel = self.bot.get_channel(self.status_channel_id)
            if not channel:
                return
            embed = await self.get_status_embed()
            if self.status_message_id:
                try:
                    msg = await channel.fetch_message(self.status_message_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound:
                    pass
            msg = await channel.send(embed=embed)
            self.status_message_id = msg.id
            self._save_status_message_id()
        except Exception as e:
            print(f"Error updating log status message: {e}")

    @tasks.loop(hours=1)
    async def auto_status(self):
        await self._update_status_message()

    @auto_status.before_loop
    async def before_auto_status(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def channel_cleanup(self):
        try:
            channel = self.bot.get_channel(self.status_channel_id)
            if not channel or not self.status_message_id:
                return
            async for msg in channel.history(limit=100):
                if msg.id != self.status_message_id:
                    try:
                        await msg.delete()
                        await asyncio.sleep(0.5)
                    except (discord.Forbidden, discord.NotFound):
                        pass
        except Exception as e:
            print(f"Error in log channel cleanup: {e}")

    @channel_cleanup.before_loop
    async def before_channel_cleanup(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def cleanup_old_logs(self):
        cutoff = datetime.now() - timedelta(days=MAX_DAYS)

        for log_file in self.log_dir.glob('discord_log_*.txt'):
            try:
                date_str = log_file.stem.split('discord_log_')[1][:10]
                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff:
                    await self.rotate_log(log_file)
            except (ValueError, IndexError):
                continue

        for archive in self.archive_dir.glob('*.gz'):
            try:
                date_str = archive.stem.split('discord_log_')[1][:10]
                if datetime.strptime(date_str, '%Y-%m-%d') < cutoff:
                    archive.unlink()
                    print(f"Deleted old archive: {archive.name}")
            except (ValueError, IndexError):
                continue

    @cleanup_old_logs.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.is_owner()
    async def logstatus(self, ctx):
        await self._update_status_message()

    @commands.command()
    @commands.is_owner()
    async def clearoldlogs(self, ctx):
        await self.cleanup_old_logs()
        await ctx.send("Done.")

    @commands.command()
    @commands.is_owner()
    async def searchlog(self, ctx, month: int, date: int, year: int):
        try:
            date_str = datetime(year, month, date).strftime('%Y-%m-%d')
        except ValueError:
            await ctx.send("Invalid date.")
            return

        MAX_SIZE = 7_340_032
        found = False

        current_log = self.log_dir / f"discord_log_{date_str}.txt"
        if current_log.exists():
            if current_log.stat().st_size <= MAX_SIZE:
                with open(current_log, 'rb') as f:
                    buf = io.BytesIO(f.read())
                await ctx.send("Current log:", file=discord.File(fp=buf, filename=f"log_{date_str}.txt"))
                found = True
            else:
                await ctx.send(f"Current log too large to send ({self.format_size(current_log.stat().st_size)}).")

        for i, archive in enumerate(sorted(self.archive_dir.glob(f"discord_log_{date_str}*.gz")), 1):
            try:
                with gzip.open(archive, 'rb') as f:
                    data = f.read()
                if len(data) <= MAX_SIZE:
                    await ctx.send(f"Archive {i}:", file=discord.File(fp=io.BytesIO(data), filename=f"log_{date_str}_{i}.txt"))
                    found = True
                else:
                    await ctx.send(f"Archive {i} too large ({self.format_size(len(data))}).")
            except Exception as e:
                await ctx.send(f"Error reading archive {i}: {e}")
            await asyncio.sleep(1)

        if not found:
            await ctx.send(f"No logs found for {date_str}.")

    # Message Events
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] [{message.guild.name}] MESSAGE - #{message.channel.name} - {message.author.name}: {message.content}"
        for a in message.attachments:
            entry += f"\nATTACHMENT: {a.url}"
        for e in message.embeds:
            entry += f"\nEMBED: {e.title}"
        await self.log_to_file(entry)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        author = message.author.name if message.author else "Unknown"
        await self.log_to_file(f"[{ts}] [{message.guild.name}] MESSAGE DELETED - {author}: {message.content}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{before.guild.name}] MESSAGE EDITED - {before.author.name}: {before.content} -> {after.content}")

    # Member Events
    @commands.Cog.listener()
    async def on_member_join(self, member):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{member.guild.name}] MEMBER JOINED - {member.name}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{member.guild.name}] MEMBER LEFT - {member.name}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []
        if before.nick != after.nick:
            changes.append(f"nickname: {before.nick} -> {after.nick}")
        added = set(after.roles) - set(before.roles)
        removed = set(before.roles) - set(after.roles)
        if added:
            changes.append(f"added roles: {', '.join(r.name for r in added)}")
        if removed:
            changes.append(f"removed roles: {', '.join(r.name for r in removed)}")
        if changes:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.log_to_file(f"[{ts}] [{before.guild.name}] MEMBER UPDATED - {before.name}: {', '.join(changes)}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{guild.name}] MEMBER BANNED - {user.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{guild.name}] MEMBER UNBANNED - {user.name}")

    # Voice Events
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if after.channel:
            await self.log_to_file(f"[{ts}] [{member.guild.name}] VOICE JOIN - {member.name} joined {after.channel.name}")
        else:
            await self.log_to_file(f"[{ts}] [{member.guild.name}] VOICE LEFT - {member.name} left {before.channel.name}")

    # Channel Events
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{channel.guild.name}] CHANNEL CREATED - #{channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{channel.guild.name}] CHANNEL DELETED - #{channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.category != after.category:
            changes.append(f"category: {before.category} -> {after.category}")
        if changes:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.log_to_file(f"[{ts}] [{before.guild.name}] CHANNEL UPDATED - #{before.name}: {', '.join(changes)}")

    # Role Events
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{role.guild.name}] ROLE CREATED - {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{role.guild.name}] ROLE DELETED - {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.color != after.color:
            changes.append(f"color: {before.color} -> {after.color}")
        if before.permissions != after.permissions:
            changes.append("permissions changed")
        if changes:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.log_to_file(f"[{ts}] [{before.guild.name}] ROLE UPDATED - {before.name}: {', '.join(changes)}")

    # Guild Events
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.icon != after.icon:
            changes.append("icon changed")
        if before.banner != after.banner:
            changes.append("banner changed")
        if changes:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.log_to_file(f"[{ts}] [{before.name}] SERVER UPDATED - {', '.join(changes)}")

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added = set(after) - set(before)
        removed = set(before) - set(after)
        if added:
            await self.log_to_file(f"[{ts}] [{guild.name}] EMOJIS ADDED - {', '.join(str(e) for e in added)}")
        if removed:
            await self.log_to_file(f"[{ts}] [{guild.name}] EMOJIS REMOVED - {', '.join(str(e) for e in removed)}")

    # Thread Events
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{thread.guild.name}] THREAD CREATED - #{thread.name} in #{thread.parent.name}")

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.log_to_file(f"[{ts}] [{thread.guild.name}] THREAD DELETED - #{thread.name}")

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.archived != after.archived:
            changes.append(f"archived: {before.archived} -> {after.archived}")
        if before.locked != after.locked:
            changes.append(f"locked: {before.locked} -> {after.locked}")
        if changes:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.log_to_file(f"[{ts}] [{before.guild.name}] THREAD UPDATED - #{before.name}: {', '.join(changes)}")

    # Sticker Events
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added = set(after) - set(before)
        removed = set(before) - set(after)
        if added:
            await self.log_to_file(f"[{ts}] [{guild.name}] STICKERS ADDED - {', '.join(s.name for s in added)}")
        if removed:
            await self.log_to_file(f"[{ts}] [{guild.name}] STICKERS REMOVED - {', '.join(s.name for s in removed)}")


async def setup(bot):
    await bot.add_cog(LogManager(bot))
