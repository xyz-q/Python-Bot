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
        self.max_file_size = 128 * 1024 * 1024  # 128MB before rotation
        self.max_days = 30  # Days to keep logs
        self.check_interval = 24  # Hours between cleanup checks
        self.status_channel_id = 1337674275427061871  # Add this line
        self.status_interval = 12  # Hours between status updates, adjust as needed
        
        # Setup directories
        self.log_dir = Path('logs')
        self.archive_dir = self.log_dir / 'archived'
        self.log_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        
        # Start background tasks
        self.cleanup_old_logs.start()
        self.auto_status.start()  # Add this line

    def cog_unload(self):
        self.cleanup_old_logs.cancel()
        self.auto_status.cancel()  # Add this line

    def format_size(self, size_bytes):
        """Convert bytes to human readable format like Windows"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024

    def get_directory_size(self, directory):
        """Calculate total size of a directory"""
        total = 0
        try:
            for entry in os.scandir(directory):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_directory_size(entry.path)
        except Exception as e:
            print(f"Error calculating size for {directory}: {e}")
        return total

    async def get_status_embed(self):
        """Create status embed for logging system"""
        # Calculate total bot size (all cogs and files)
        bot_total_size = self.get_directory_size('.')  # Current directory
        
        # Calculate logging specific sizes
        logs_current_size = 0
        logs_archive_size = 0
        num_files = 0
        num_archives = 0
        
        # Get current log files info
        for log_file in self.log_dir.glob('*.txt'):
            file_size = log_file.stat().st_size
            logs_current_size += file_size
            num_files += 1
            
        # Get archived files info
        for archive in self.archive_dir.glob('*.gz'):
            file_size = archive.stat().st_size
            logs_archive_size += file_size
            num_archives += 1

        logs_total_size = logs_current_size + logs_archive_size

        embed = discord.Embed(
            title="📊 Log Status",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        # Total Bot Storage
        embed.add_field(
            name="Total Bot Storage",
            value=f"Size: `{self.format_size(bot_total_size)}`",
            inline=False
        )

               
        # File Counts
        embed.add_field(
            name="Log Files", 
            value=f"Current: `{num_files}`\n"
                  f"Archived: `{num_archives}`\n"
                  f"Total: `{num_files + num_archives}`",
            inline=True
        )
                
        # Logging System Status
        embed.add_field(
            name="Logging System",
            value=f"Current: `{self.format_size(logs_current_size)}`\n"
                  f"Archives: `{self.format_size(logs_archive_size)}`\n"
                  f"Total Logs: `{self.format_size(logs_total_size)}`\n",
            inline=True
        )
        # Settings

        
        # Add last update time
        embed.set_footer(text="Last Updated")
        
        return embed

    async def should_send_status(self, channel):
        """Check if enough time has passed since last status message"""
        try:
            # Get the last message in the channel
            messages = [msg async for msg in channel.history(limit=1)]
            if not messages:
                return True  # No messages found, okay to send

            last_message = messages[0]
            time_since_last = datetime.now(last_message.created_at.tzinfo) - last_message.created_at
            hours_since_last = time_since_last.total_seconds() / 3600

            # Check if it's been long enough since the last message
            return hours_since_last >= self.status_interval
        except Exception as e:
            print(f"Error checking message history: {e}")
            return False

    @tasks.loop(hours=1)  # Check every hour
    async def auto_status(self):
        """Automatically post status updates if enough time has passed"""
        try:
            channel = self.bot.get_channel(self.status_channel_id)
            if channel and await self.should_send_status(channel):
                embed = await self.get_status_embed()
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Error in auto_status: {e}")

    @auto_status.before_loop
    async def before_auto_status(self):
        await self.bot.wait_until_ready()

    # Update the existing logstatus command to use the new embed
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logstatus(self, ctx):
        """Show status of logging system"""
        embed = await self.get_status_embed()
        await ctx.send(embed=embed)

    # Add a command to change the status channel
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setstatuschannel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for automatic status updates"""
        if channel is None:
            channel = ctx.channel
        
        self.status_channel_id = channel.id
        await ctx.send(f"Status updates will now be sent to {channel.mention}")

    # Add a command to change the status interval

            
        self.status_interval = hours
        self.auto_status.change_interval(hours=hours)
        await ctx.send(f"Status update interval changed to {hours} hours")


    async def log_to_file(self, log_entry: str):
        """Write log entry and check for daily rotation"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f"discord_log_{current_date}.txt"
        
        # Check for previous day's log and rotate it
        for old_log in self.log_dir.glob('*.txt'):
            if old_log.name != log_file.name:  # If it's not today's log file
                await self.rotate_log(old_log)
            
        # Write new log entry
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")


    async def rotate_log(self, log_file: Path):
        """Compress and archive the log file"""
        try:
            if not log_file.exists() or log_file.stat().st_size == 0:
                return
                
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            archive_name = self.archive_dir / f"{log_file.stem}_{timestamp}.gz"
            
            # Compress the file
            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_name, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify the archive was created successfully
            if archive_name.exists() and archive_name.stat().st_size > 0:
                # Remove the original file after successful compression
                log_file.unlink()
                print(f"Successfully archived {log_file} to {archive_name}")
            else:
                print(f"Failed to create archive for {log_file}")
                
        except Exception as e:
            print(f"Error archiving log file {log_file}: {e}")


    @tasks.loop(hours=24)
    async def cleanup_old_logs(self):
        """Remove logs older than max_days"""
        cutoff_date = datetime.now() - timedelta(days=self.max_days)
        
        # Check archived logs
        for archive_file in self.archive_dir.glob('*.gz'):
            try:
                # Extract date from filename (discord_log_2024-01-20_15-30-45.gz)
                date_str = archive_file.stem.split('_')[2]  # Gets YYYY-MM-DD
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    print(f"Removing old archive: {archive_file}")
                    archive_file.unlink()
            except (ValueError, IndexError) as e:
                print(f"Error processing archive file {archive_file}: {e}")
                continue
                
        # Also check current logs
        for log_file in self.log_dir.glob('*.txt'):
            try:
                date_str = log_file.stem.split('_')[2]  # Gets YYYY-MM-DD
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    print(f"Rotating old log: {log_file}")
                    await self.rotate_log(log_file)
            except (ValueError, IndexError) as e:
                print(f"Error processing log file {log_file}: {e}")
                continue


    @cleanup_old_logs.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


    # All your existing event listeners:
    # Message Events
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{message.guild.name}] MESSAGE - #{message.channel.name} - {message.author.name}: {message.content}"
        
        if message.attachments:
            for attachment in message.attachments:
                log_entry += f"\nATTACHMENT: {attachment.url}"
        
        if message.embeds:
            for embed in message.embeds:
                log_entry += f"\nEMBED: {embed.title}"

        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if message.guild exists
            guild_name = message.guild.name if message.guild else "Direct Message"
            
            # Check if message.author exists
            author_name = message.author.name if message.author else "Unknown User"
            
            log_entry = f"[{timestamp}] [{guild_name}] MESSAGE DELETED - {author_name}: {message.content}"
            await self.log_to_file(log_entry)
        except Exception as e:
            # Safely handle any errors that might occur during logging
            print(f"Error logging deleted message: {e}")


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{before.guild.name}] MESSAGE EDITED - {before.author.name}: {before.content} -> {after.content}"
        await self.log_to_file(log_entry)

    # Member Events
    @commands.Cog.listener()
    async def on_member_join(self, member):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{member.guild.name}] MEMBER JOINED - {member.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{member.guild.name}] MEMBER LEFT - {member.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.nick != after.nick:
            changes.append(f"nickname: {before.nick} -> {after.nick}")
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            if added_roles:
                changes.append(f"added roles: {', '.join(role.name for role in added_roles)}")
            if removed_roles:
                changes.append(f"removed roles: {', '.join(role.name for role in removed_roles)}")
                
        if changes:
            log_entry = f"[{timestamp}] [{before.guild.name}] MEMBER UPDATED - {before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{guild.name}] MEMBER BANNED - {user.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{guild.name}] MEMBER UNBANNED - {user.name}"
        await self.log_to_file(log_entry)

    # Voice Events
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if before.channel != after.channel:
            if after.channel:
                log_entry = f"[{timestamp}] [{member.guild.name}] VOICE JOIN - {member.name} joined {after.channel.name}"
            else:
                log_entry = f"[{timestamp}] [{member.guild.name}] VOICE LEFT - {member.name} left {before.channel.name}"
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



    # Channel Events
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{channel.guild.name}] CHANNEL CREATED - #{channel.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{channel.guild.name}] CHANNEL DELETED - #{channel.name}"
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
            log_entry = f"[{timestamp}] [{before.guild.name}] CHANNEL UPDATED - #{before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    # Role Events
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{role.guild.name}] ROLE CREATED - {role.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{role.guild.name}] ROLE DELETED - {role.name}"
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
            log_entry = f"[{timestamp}] [{before.guild.name}] ROLE UPDATED - {before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    # Guild/Server Events
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
            log_entry = f"[{timestamp}] [{before.name}] SERVER UPDATED - changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added_emojis = set(after) - set(before)
        removed_emojis = set(before) - set(after)
        
        if added_emojis:
            log_entry = f"[{timestamp}] [{guild.name}] EMOJIS ADDED - {', '.join(str(emoji) for emoji in added_emojis)}"
            await self.log_to_file(log_entry)
        if removed_emojis:
            log_entry = f"[{timestamp}] [{guild.name}] EMOJIS REMOVED - {', '.join(str(emoji) for emoji in removed_emojis)}"
            await self.log_to_file(log_entry)


    # Thread Events
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{thread.guild.name}] THREAD CREATED - #{thread.name} in #{thread.parent.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{thread.guild.name}] THREAD DELETED - #{thread.name}"
        await self.log_to_file(log_entry)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes = []
        
        if before.name != after.name:
            changes.append(f"name: {before.name} -> {after.name}")
        if before.archived != after.archived:
            changes.append(f"archived: {before.archived} -> {after.archived}")
        if before.locked != after.locked:
            changes.append(f"locked: {before.locked} -> {after.locked}")
            
        if changes:
            log_entry = f"[{timestamp}] [{before.guild.name}] THREAD UPDATED - #{before.name} changes: {', '.join(changes)}"
            await self.log_to_file(log_entry)

    # Sticker Events
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added_stickers = set(after) - set(before)
        removed_stickers = set(before) - set(after)
        
        if added_stickers:
            log_entry = f"[{timestamp}] [{guild.name}] STICKERS ADDED - {', '.join(sticker.name for sticker in added_stickers)}"
            await self.log_to_file(log_entry)
        if removed_stickers:
            log_entry = f"[{timestamp}] [{guild.name}] STICKERS REMOVED - {', '.join(sticker.name for sticker in removed_stickers)}"
            await self.log_to_file(log_entry)

    # Commands and Error Handling


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearoldlogs(self, ctx):
        """Manually trigger cleanup of old logs"""
        try:
            await self.cleanup_old_logs()
            await ctx.send("Old logs have been cleaned up successfully.")
        except Exception as e:
            await ctx.send(f"Error cleaning up logs: {str(e)}")


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def searchlog(self, ctx, month: int, date: int, year: int):
        """Search for and send log file for specific date"""
        try:
            # Format the date to match log file naming
            search_date = datetime(year, month, date)
            date_str = search_date.strftime('%Y-%m-%d')
            
            found_logs = False
            
            # Check current logs folder first
            current_log = self.log_dir / f"discord_log_{date_str}.txt"
            if current_log.exists():
                try:
                    await ctx.send("Current log:", file=discord.File(current_log))
                    found_logs = True
                    await asyncio.sleep(1)  # Add small delay between sends
                except discord.HTTPException as e:
                    await ctx.send(f"Error sending current log: {str(e)}")

            # Check archives for any logs from that day
            archives = list(self.archive_dir.glob(f"discord_log_{date_str}*.gz"))
            for i, archive in enumerate(archives, 1):
                temp_file = self.log_dir / f"temp_{date_str}_{i}.txt"
                
                try:
                    # Decompress the archive
                    with gzip.open(archive, 'rb') as f_in:
                        with open(temp_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Send file with number if multiple archives exist
                    message = f"Archive {i}:" if len(archives) > 1 else "Archive:"
                    await ctx.send(message, file=discord.File(str(temp_file)))
                    found_logs = True
                    await asyncio.sleep(1)  # Add small delay between sends
                    
                except discord.HTTPException as e:
                    await ctx.send(f"Error sending archive {i}: {str(e)}")
                finally:
                    # Clean up temp file
                    if temp_file.exists():
                        temp_file.unlink()

            if not found_logs:
                await ctx.send(f"No logs found for {date_str}")
                
        except ValueError:
            await ctx.send("Invalid date format. Please use: ,searchlog month date year\nExample: ,searchlog 1 15 2024")
        except Exception as e:
            await ctx.send(f"Error searching logs: {str(e)}")












async def setup(bot):
    await bot.add_cog(LogManager(bot))
