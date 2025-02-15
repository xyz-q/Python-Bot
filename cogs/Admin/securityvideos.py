import discord
from discord.ext import commands, tasks
import subprocess
import os
import json
from datetime import datetime

class StorageMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_path = "/home/user/backups"
        self.channel_id = 1337733172242157600
        self.message_id = None
        self.storage_limit = 1024 * 1024 * 1024 * 500  # 500GB in bytes
        self.stats_file = ".json/backup_stats.json"
        self.last_stats = self.load_stats()
        self.monitor_storage.start()

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

    @tasks.loop(minutes=5)
    async def monitor_storage(self):
        """Continuously monitors storage and updates the embed"""
        try:
            message = await self.get_or_create_message()
            if not message:
                return

            storage_info = self.get_storage_info()
            
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



async def setup(bot):
    await bot.add_cog(StorageMonitor(bot))
