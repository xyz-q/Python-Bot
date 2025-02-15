import discord
from discord.ext import commands, tasks
import subprocess
import os
from datetime import datetime

class StorageMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_path = "/home/user/backups"
        self.channel_id = 1337733172242157600
        self.message_id = None
        self.monitor_storage.start()

    def get_directory_size(self, path):
        """Get the size of a directory and its contents in bytes"""
        try:
            result = subprocess.run(['du', '-sb', path], capture_output=True, text=True)
            size = int(result.stdout.split()[0])
            return size
        except:
            return 0

    def get_subdirectory_sizes(self, path):
        """Get sizes of all subdirectories"""
        try:
            result = subprocess.run(['du', '-h', '--max-depth=1', path], 
                                  capture_output=True, text=True)
            return result.stdout.strip().split('\n')
        except:
            return []

    def get_disk_usage(self, path):
        """Get disk usage information"""
        try:
            result = subprocess.run(['df', '-h', path], 
                                  capture_output=True, text=True)
            return result.stdout.strip().split('\n')[1]
        except:
            return None

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

            embed = discord.Embed(
                title="Storage Monitor",
                description="📊 Storage Status",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )

            # Get disk usage
            disk_usage = self.get_disk_usage(self.backup_path)
            if disk_usage:
                parts = disk_usage.split()
                embed.add_field(
                    name="Disk Usage",
                    value=f"💾 Total: {parts[1]}\n"
                          f"📦 Used: {parts[2]} ({parts[4]})\n"
                          f"✨ Free: {parts[3]}",
                    inline=False
                )

            # Get directory sizes
            dir_sizes = self.get_subdirectory_sizes(self.backup_path)
            
            # Format directory information
            dirs_info = ""
            for line in dir_sizes:
                size, path = line.split('\t')
                if path != self.backup_path:  # Skip the total
                    dir_name = os.path.basename(path)
                    dirs_info += f"📁 {dir_name}: {size}\n"

            if dirs_info:
                embed.add_field(
                    name="Directory Sizes",
                    value=f"```{dirs_info}```",
                    inline=False
                )

            # Get file count
            try:
                file_count = sum([len(files) for r, d, files in os.walk(self.backup_path)])
                embed.add_field(
                    name="Total Files",
                    value=f"📄 {file_count} files",
                    inline=True
                )
            except:
                pass

            # Add next update time
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

    @commands.command()
    async def reset_monitor(self, ctx):
        """Resets the storage monitor message"""
        self.message_id = None
        await ctx.send("Storage monitor reset. A new message will be created on next update.")

async def setup(bot):
    await bot.add_cog(StorageMonitor(bot))
