import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import gzip
from pathlib import Path
import shutil
import asyncio

class LogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB before rotation
        self.max_days = 30  # Days to keep logs
        self.check_interval = 24  # Hours between cleanup checks
        
        # Setup directories
        self.log_dir = Path('logs')
        self.archive_dir = self.log_dir / 'archived'
        self.log_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        
        # Start background tasks
        self.cleanup_old_logs.start()

    def cog_unload(self):
        self.cleanup_old_logs.cancel()

    async def log_to_file(self, log_entry: str):
        """Write log entry and handle rotation if needed"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f"discord_log_{current_date}.txt"
        
        # Check if file needs rotation
        if log_file.exists() and log_file.stat().st_size >= self.max_file_size:
            await self.rotate_log(log_file)
            
        # Write new log entry
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    async def rotate_log(self, log_file: Path):
        """Compress and archive the current log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        archive_name = self.archive_dir / f"{log_file.stem}_{timestamp}.gz"
        
        # Compress the file
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Clear the original file
        log_file.write_text('')

    @tasks.loop(hours=24)
    async def cleanup_old_logs(self):
        """Remove logs older than max_days"""
        cutoff_date = datetime.now() - timedelta(days=self.max_days)
        
        # Check archived logs
        for archive_file in self.archive_dir.glob('*.gz'):
            try:
                date_str = archive_file.stem.split('_')[2]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    archive_file.unlink()
            except (ValueError, IndexError):
                continue

    @cleanup_old_logs.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    # All your existing event listeners:
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message.guild.name} #{message.channel.name} - {message.author.name}: {message.content}"
        
        if message.attachments:
            for attachment in message.attachments:
                log_entry += f"\nATTACHMENT: {attachment.url}"
        
        if message.embeds:
            for embed in message.embeds:
                log_entry += f"\nEMBED: {embed.title}"

        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MEMBER JOINED - {member.name} joined {member.guild.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MEMBER LEFT - {member.name} left {member.guild.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MESSAGE DELETED - {message.author.name}: {message.content}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MESSAGE EDITED - {before.author.name}: {before.content} -> {after.content}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if before.channel != after.channel:
            if after.channel:
                log_entry = f"[{timestamp}] VOICE JOIN - {member.name} joined {after.channel.name}"
            else:
                log_entry = f"[{timestamp}] VOICE LEFT - {member.name} left {before.channel.name}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] CHANNEL CREATED - #{channel.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] CHANNEL DELETED - #{channel.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ROLE CREATED - {role.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] ROLE DELETED - {role.name}"
        await self.log_to_file(log_entry)



    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.position != after.position:
            changes.append(f"position: {before.position} -> {after.position}")
        if before.category != after.category:
            changes.append(f"category: {before.category} -> {after.category}")
            
        if changes:
            log_entry = f"[{timestamp}] CHANNEL UPDATED - #{before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.color != after.color:
            changes.append(f"color: {before.color} -> {after.color}")
        if before.permissions != after.permissions:
            changes.append("permissions changed")
            
        if changes:
            log_entry = f"[{timestamp}] ROLE UPDATED - {before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.nick != after.nick:
            changes.append(f"nickname: {before.nick} -> {after.nick}")
        if before.roles != after.roles:
            # Find which roles were added/removed
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            if added_roles:
                changes.append(f"added roles: {', '.join(role.name for role in added_roles)}")
            if removed_roles:
                changes.append(f"removed roles: {', '.join(role.name for role in removed_roles)}")
                
        if changes:
            log_entry = f"[{timestamp}] MEMBER UPDATED - {before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MEMBER BANNED - {user.name} from {guild.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] MEMBER UNBANNED - {user.name} from {guild.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.icon != after.icon:
            changes.append("icon changed")
        if before.banner != after.banner:
            changes.append("banner changed")
            
        if changes:
            log_entry = f"[{timestamp}] SERVER UPDATED - {before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] THREAD CREATED - #{thread.name} in #{thread.parent.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] THREAD DELETED - #{thread.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added_emojis = set(after) - set(before)
        removed_emojis = set(before) - set(after)
        
        if added_emojis:
            log_entry = f"[{timestamp}] EMOJIS ADDED - {', '.join(str(emoji) for emoji in added_emojis)}"
            await self.log_to_file(log_entry)
        if removed_emojis:
            log_entry = f"[{timestamp}] EMOJIS REMOVED - {', '.join(str(emoji) for emoji in removed_emojis)}"
            await self.log_to_file(log_entry)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logstatus(self, ctx):
        """Show status of logging system"""
        total_size = 0
        num_files = 0
        num_archives = 0
        
        for log_file in self.log_dir.glob('*.txt'):
            total_size += log_file.stat().st_size
            num_files += 1
            
        for archive in self.archive_dir.glob('*.gz'):
            total_size += archive.stat().st_size
            num_archives += 1
            
        status = f"""
        **Logging System Status**
        Current Log Files: {num_files}
        Archived Files: {num_archives}
        Total Size: {total_size / 1024 / 1024:.2f} MB
        Max File Size: {self.max_file_size / 1024 / 1024} MB
        Retention Period: {self.max_days} days
        """
        
        await ctx.send(status)

async def setup(bot):
    await bot.add_cog(LogManager(bot))
