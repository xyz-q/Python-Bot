import discord
from discord.ext import commands, tasks
import subprocess
import os
import json
from datetime import datetime, time
import asyncio
import time
class StorageMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_path = "/home/user/backups"
        self.channel_id = 1337733172242157600
        self.message_id = None
        self.storage_limit = 1024 * 1024 * 1024 * 10  # Your existing limit
        self.stats_file = ".json/backup_stats.json"
        self.last_stats = self.load_stats()
        self.deleted_files_log = []  # Add this line
        self.monitor_storage.start()
        self.cleanup_storage.start()  # Add this line

    def load_stats(self):
        """Load previous stats from JSON file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading stats: {e}")
        return {
            'total_size': 0,
            'file_count': 0,
            'directories': {},
            'last_update': None
        }

    def save_stats(self, stats):
        """Save current stats to JSON file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def get_directory_size(self, path):
        """Get the size of a directory and its contents in bytes"""
        try:
            result = subprocess.run(['du', '-sb', path], capture_output=True, text=True)
            size = int(result.stdout.split()[0])
            return size
        except:
            return 0

    def get_subdirectory_sizes(self, path):
        """Get sizes and details of all subdirectories"""
        dirs_info = {}
        try:
            result = subprocess.run(['du', '-sb', '--max-depth=1', path], 
                                  capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                size, dir_path = line.split('\t')
                if dir_path != path:
                    dir_name = os.path.basename(dir_path)
                    dirs_info[dir_name] = int(size)
            return dirs_info
        except:
            return {}

    def format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def format_size_change(self, change_bytes):
        """Format size change with + or - prefix"""
        prefix = '+' if change_bytes >= 0 else ''
        return f"{prefix}{self.format_size(change_bytes)}"

    def get_storage_info(self):
        """Get current storage information and changes"""
        current_size = self.get_directory_size(self.backup_path)
        current_dirs = self.get_subdirectory_sizes(self.backup_path)
        current_files = sum([len(files) for r, d, files in os.walk(self.backup_path)])
        
        # Calculate changes
        size_change = current_size - self.last_stats['total_size']
        file_change = current_files - self.last_stats['file_count']
        
        # Calculate directory changes
        dir_changes = {}
        for dir_name, size in current_dirs.items():
            old_size = self.last_stats['directories'].get(dir_name, 0)
            if size != old_size:
                dir_changes[dir_name] = size - old_size

        # Update last stats
        current_stats = {
            'total_size': current_size,
            'file_count': current_files,
            'directories': current_dirs,
            'last_update': datetime.utcnow().isoformat()
        }
        self.save_stats(current_stats)
        
        return {
            'total': self.format_size(self.storage_limit),
            'used': self.format_size(current_size),
            'free': self.format_size(self.storage_limit - current_size),
            'percent': f"{(current_size / self.storage_limit) * 100:.1f}%",
            'size_change': self.format_size_change(size_change),
            'file_count': current_files,
            'file_change': file_change,
            'dir_changes': {k: self.format_size_change(v) for k, v in dir_changes.items()},
            'directories': current_dirs
        }

    async def get_or_create_message(self):
        """Gets existing message or creates new one in the specified channel"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel is None:
                print(f"Warning: Could not find channel {self.channel_id}")
                return None

            # Delete all messages except our stored message
            async for message in channel.history(limit=100):
                if self.message_id is None or message.id != self.message_id:
                    try:
                        await message.delete()
                        await asyncio.sleep(0.5)  # Prevent rate limiting
                    except Exception as e:
                        print(f"Error deleting message: {e}")

            # Try to fetch existing message
            if self.message_id:
                try:
                    return await channel.fetch_message(self.message_id)
                except:
                    self.message_id = None

            # Create new message if needed
            embed = discord.Embed(
                title="Storage Monitor",
                description="📊 Initializing...",
                color=discord.Color.blue()
            )
            message = await channel.send(embed=embed)
            self.message_id = message.id
            return message

        except Exception as e:
            print(f"Error in get_or_create_message: {e}")
            return None

    @tasks.loop(minutes=45)
    async def monitor_storage(self):
        """Continuously monitors storage and updates the embed"""
        try:
            message = await self.get_or_create_message()
            if not message:
                return

            storage_info = self.get_storage_info()
            
            # Calculate total size of deleted files
            total_deleted_size = 0
            age_count = 0
            size_count = 0
            
            for deletion in self.deleted_files_log:
                # Convert the size string back to bytes
                size_str = deletion['size']
                if 'GB' in size_str:
                    size = float(size_str.replace(' GB', '')) * 1024 * 1024 * 1024
                elif 'MB' in size_str:
                    size = float(size_str.replace(' MB', '')) * 1024 * 1024
                elif 'KB' in size_str:
                    size = float(size_str.replace(' KB', '')) * 1024
                else:
                    size = float(size_str.replace(' B', ''))
                
                total_deleted_size += size
                if deletion['reason'] == 'age':
                    age_count += 1
                elif deletion['reason'] == 'size':
                    size_count += 1

            # Format the total deleted size
            deleted_size_formatted = self.format_size(total_deleted_size)

            
            embed = discord.Embed(
                title="Storage Monitor",
                description="📊 Storage Status",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )

            # Storage usage field
            embed.add_field(
                name="Storage Usage",
                value=f"💾 Limit: {storage_info['total']}\n"
                      f"📦 Used: {storage_info['used']} ({storage_info['percent']})\n"
                      f"✨ Free: {storage_info['free']}\n"
                      f"📈 Change: {storage_info['size_change']}",
                inline=False
            )

            # Files information
            embed.add_field(
                name="Files",
                value=f"📄 Total: {storage_info['file_count']}\n"
                      f"📊 Change: {'+' if storage_info['file_change'] >= 0 else ''}{storage_info['file_change']}",
                inline=False
            )

            # Directory sizes and changes
            dirs_info = ""
            for dir_name, size in storage_info['directories'].items():
                change = storage_info['dir_changes'].get(dir_name, "no change")
                dirs_info += f"📁 {dir_name}: {self.format_size(size)} ({change})\n"

            if dirs_info:
                embed.add_field(
                    name="Directory Sizes",
                    value=f"```{dirs_info}```",
                    inline=False
                )

            # Add recent deletions field if there are any
            if hasattr(self, 'deleted_files_log') and self.deleted_files_log:
                deletion_summary = (
                    f"Total Deleted: {deleted_size_formatted}\n"
                    f"Files Removed: {age_count + size_count}\n"
                    f"- Age-based: {age_count}\n"
                    f"- Size-based: {size_count}"
                )
                embed.add_field(
                    name="Recent Cleanup Summary",
                    value=f"```{deletion_summary}```",
                    inline=False
                )

            # Set color based on usage percentage
            usage_pct = float(storage_info['percent'].strip('%'))
            if usage_pct >= 90:
                embed.color = discord.Color.red()
            elif usage_pct >= 75:
                embed.color = discord.Color.orange()
            else:
                embed.color = discord.Color.green()

            embed.set_footer(text="Next update in 5 minutes")
            await message.edit(embed=embed)




        except Exception as e:
            print(f"Error in monitor_storage: {e}")
            if message:
                error_embed = discord.Embed(
                    title="Storage Monitor Error",
                    description=f"❌ Error monitoring storage: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                error_embed.set_footer(text="Will retry in 5 minutes")
                await message.edit(embed=error_embed)




    @monitor_storage.before_loop
    async def before_monitor(self):
        """Wait until the bot is ready before starting the monitor"""
        await self.bot.wait_until_ready()



    async def cleanup_old_files(self):
        """Delete files older than 7 days"""
        deleted = []
        print("\n=== Starting age-based cleanup ===")
        print(f"Checking for files older than 7 days in {self.backup_path}")
        
        for root, _, filenames in os.walk(self.backup_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                try:
                    file_age = time.time() - os.path.getmtime(filepath)
                    age_days = file_age / (24 * 3600)
                    file_size = os.path.getsize(filepath)
                    
                    print(f"\nChecking file: {filename}")
                    print(f"Age: {age_days:.1f} days")
                    print(f"Size: {self.format_size(file_size)}")
                    
                    if age_days > 7:  # 7 days old
                        print(f"🗑️ Deleting {filename} (Too old: {age_days:.1f} days)")
                        os.remove(filepath)
                        deleted.append({
                            'path': os.path.relpath(filepath, self.backup_path),
                            'size': self.format_size(file_size),
                            'age': f"{age_days:.1f} days",
                            'reason': 'age'
                        })
                    else:
                        print(f"✅ Keeping {filename} (Age OK)")
                except Exception as e:
                    print(f"❌ Error processing {filepath}: {e}")
        
        print(f"\nAge cleanup complete. Deleted {len(deleted)} files")
        return deleted
    
    async def cleanup_excess_storage(self):
        """Delete oldest files until under storage limit"""
        current_size = self.get_directory_size(self.backup_path)
        print("\n=== Starting size-based cleanup ===")
        print(f"Current total size: {self.format_size(current_size)}")
        print(f"Size limit: {self.format_size(self.storage_limit)}")
        
        if current_size <= self.storage_limit:
            print("Storage usage within limits, no cleanup needed")
            return []

        deleted = []
        files = []
        
        # Gather all files with their info
        print("\nGathering file information...")
        for root, _, filenames in os.walk(self.backup_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    size = os.path.getsize(filepath)
                    files.append({
                        'path': filepath,
                        'name': filename,
                        'mtime': mtime,
                        'size': size,
                        'age': (time.time() - mtime) / (24 * 3600)
                    })
                except Exception as e:
                    print(f"❌ Error getting info for {filepath}: {e}")

        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x['mtime'])
        print(f"\nFound {len(files)} files, sorted by age")

        # Delete oldest files until under limit
        for file_info in files:
            if current_size <= self.storage_limit:
                break

            try:
                print(f"\nNeed to remove more files. Currently at: {self.format_size(current_size)}")
                print(f"🗑️ Deleting {file_info['name']}")
                print(f"Age: {file_info['age']:.1f} days")
                print(f"Size: {self.format_size(file_info['size'])}")
                
                os.remove(file_info['path'])
                deleted.append({
                    'path': os.path.relpath(file_info['path'], self.backup_path),
                    'size': self.format_size(file_info['size']),
                    'age': f"{file_info['age']:.1f} days",
                    'reason': 'space'
                })
                current_size -= file_info['size']
            except Exception as e:
                print(f"❌ Error deleting {file_info['path']}: {e}")

        print(f"\nSize cleanup complete. Deleted {len(deleted)} files")
        print(f"Final size: {self.format_size(self.get_directory_size(self.backup_path))}")
        return deleted


    @tasks.loop(minutes=45)
    async def cleanup_storage(self):
        """Main cleanup task"""
        try:

            
            # Gather all files with their info
            files = []
            total_size = 0

            
            for root, _, filenames in os.walk(self.backup_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        mtime = os.path.getmtime(filepath)
                        size = os.path.getsize(filepath)
                        age_days = (time.time() - mtime) / (24 * 3600)
                        
                        files.append({
                            'path': filepath,
                            'name': filename,
                            'size': size,
                            'age': age_days
                        })
                        total_size += size
                    except Exception as e:
                        print(f"❌ Error getting info for {filepath}: {e}")

            # Sort files by size (largest first)
            large_files = sorted(files, key=lambda x: x['size'], reverse=True)
            # Sort files by age (oldest first)
            old_files = sorted(files, key=lambda x: x['age'], reverse=True)


            for f in large_files[:5]:  # Show top 5 largest
                print(f"- {f['name']}: {self.format_size(f['size'])} ({f['age']:.1f} days old)")
            

            for f in old_files[:5]:  # Show top 5 oldest
                print(f"- {f['name']}: {f['age']:.1f} days old ({self.format_size(f['size'])})")

            deleted = []

            # First delete old files (over 7 days)
            for file_info in old_files:
                if file_info['age'] > 7:
                    try:
                        print(f"\n🗑️ Deleting {file_info['name']} (Age: {file_info['age']:.1f} days)")
                        os.remove(file_info['path'])
                        deleted.append({
                            'path': os.path.relpath(file_info['path'], self.backup_path),
                            'size': self.format_size(file_info['size']),
                            'age': f"{file_info['age']:.1f} days",
                            'reason': 'age'
                        })
                        total_size -= file_info['size']
                    except Exception as e:
                        print(f"❌ Error deleting {file_info['path']}: {e}")

            # Then delete largest files if still over limit
            if total_size > self.storage_limit:
                print(f"\nStill over limit ({self.format_size(total_size)}), removing largest files...")
                for file_info in large_files:
                    if total_size <= self.storage_limit:
                        break
                        
                    # Skip if already deleted
                    if any(d['path'] == os.path.relpath(file_info['path'], self.backup_path) for d in deleted):
                        continue

                    try:
                        print(f"\n🗑️ Deleting {file_info['name']} (Size: {self.format_size(file_info['size'])})")
                        os.remove(file_info['path'])
                        deleted.append({
                            'path': os.path.relpath(file_info['path'], self.backup_path),
                            'size': self.format_size(file_info['size']),
                            'age': f"{file_info['age']:.1f} days",
                            'reason': 'size'
                        })
                        total_size -= file_info['size']
                    except Exception as e:
                        print(f"❌ Error deleting {file_info['path']}: {e}")


            
            if deleted:
                self.deleted_files_log = (deleted + getattr(self, 'deleted_files_log', []))[:20]
                print("\nUpdating monitor message with deletion information...")
                await self.monitor_storage()

                
        except Exception as e:
            print(f"\n❌ Error in cleanup_storage: {e}")


    @cleanup_storage.before_loop
    async def before_cleanup(self):
        """Wait until the bot is ready before starting the cleanup"""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StorageMonitor(bot))
