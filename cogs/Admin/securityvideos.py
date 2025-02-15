import discord
from discord.ext import commands
import subprocess
import os
from datetime import datetime

class StorageMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_path = "/home/user/backups"

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

    def format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    @commands.command()
    async def storage(self, ctx):
        """View backup storage information"""
        try:
            # Create initial embed
            embed = discord.Embed(
                title="Backup Storage Monitor",
                description="📊 Analyzing storage...",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            message = await ctx.send(embed=embed)

            # Get disk usage
            disk_usage = self.get_disk_usage(self.backup_path)
            if disk_usage:
                parts = disk_usage.split()
                embed.add_field(
                    name="Disk Usage",
                    value=f"Total: {parts[1]}\nUsed: {parts[2]} ({parts[4]})\nFree: {parts[3]}",
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
                    value=str(file_count),
                    inline=True
                )
            except:
                pass

            # Update timestamp and status
            embed.description = "📊 Storage Analysis Complete"
            embed.set_footer(text="Last Updated")
            await message.edit(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="Storage Monitor Error",
                description=f"❌ Error accessing storage information: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.command()
    async def list_backups(self, ctx, subfolder: str = ""):
        """List contents of backup folder"""
        try:
            path = os.path.join(self.backup_path, subfolder)
            if not os.path.exists(path):
                await ctx.send(f"❌ Path not found: {subfolder}")
                return

            embed = discord.Embed(
                title=f"Backup Contents: /{subfolder}" if subfolder else "Backup Contents",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )

            # Get directory listing
            items = os.listdir(path)
            
            # Separate directories and files
            dirs = [d for d in items if os.path.isdir(os.path.join(path, d))]
            files = [f for f in items if os.path.isfile(os.path.join(path, f))]

            # Add directories
            if dirs:
                dirs_text = "\n".join(f"📁 {d}" for d in sorted(dirs))
                embed.add_field(
                    name="Directories",
                    value=f"```{dirs_text}```" if dirs_text else "None",
                    inline=False
                )

            # Add files (with sizes)
            if files:
                files_text = ""
                for f in sorted(files):
                    size = os.path.getsize(os.path.join(path, f))
                    files_text += f"📄 {f} ({self.format_size(size)})\n"
                embed.add_field(
                    name="Files",
                    value=f"```{files_text}```" if files_text else "None",
                    inline=False
                )

            embed.set_footer(text=f"Total Items: {len(items)}")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error listing contents: {str(e)}")

async def setup(bot):
    await bot.add_cog(StorageMonitor(bot))
