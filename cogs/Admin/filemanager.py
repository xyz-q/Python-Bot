import os
import shutil
from discord.ext import commands
from discord import app_commands
import discord

class FileManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_directory = os.getenv('/home/user/Media_Storage')  # Set this to your allowed directory
        
    def is_safe_path(self, path):
        """Check if the path is within the allowed directory"""
        try:
            real_path = os.path.realpath(path)
            return os.path.commonpath([real_path, self.base_directory]) == self.base_directory
        except ValueError:
            return False

    @app_commands.command(name="listfiles", description="List files in a directory")
    async def list_files(self, interaction: discord.Interaction, path: str = ""):
        """List files in the specified directory"""
        full_path = os.path.join(self.base_directory, path)
        
        if not self.is_safe_path(full_path):
            await interaction.response.send_message("Access to this path is not allowed.", ephemeral=True)
            return
            
        try:
            files = os.listdir(full_path)
            if not files:
                await interaction.response.send_message("Directory is empty.", ephemeral=True)
                return
                
            file_list = "Files and directories:\n```"
            for file in files:
                file_path = os.path.join(full_path, file)
                if os.path.isdir(file_path):
                    file_list += f"📁 {file}/\n"
                else:
                    size = os.path.getsize(file_path)
                    file_list += f"📄 {file} ({size/1024:.1f} KB)\n"
            file_list += "```"
            
            await interaction.response.send_message(file_list, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="downloadfile", description="Download a file")
    async def download_file(self, interaction: discord.Interaction, filepath: str):
        """Download a file from the server"""
        full_path = os.path.join(self.base_directory, filepath)
        
        if not self.is_safe_path(full_path):
            await interaction.response.send_message("Access to this file is not allowed.", ephemeral=True)
            return
            
        try:
            if not os.path.isfile(full_path):
                await interaction.response.send_message("File not found.", ephemeral=True)
                return
                
            file = discord.File(full_path)
            await interaction.response.send_message(file=file, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="deletefile", description="Delete a file")
    async def delete_file(self, interaction: discord.Interaction, filepath: str):
        """Delete a file from the server"""
        full_path = os.path.join(self.base_directory, filepath)
        
        if not self.is_safe_path(full_path):
            await interaction.response.send_message("Access to this file is not allowed.", ephemeral=True)
            return
            
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
                await interaction.response.send_message(f"File {filepath} deleted successfully.", ephemeral=True)
            else:
                await interaction.response.send_message("File not found.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="movefile", description="Move a file to another location")
    async def move_file(self, interaction: discord.Interaction, source: str, destination: str):
        """Move a file to another location"""
        source_path = os.path.join(self.base_directory, source)
        dest_path = os.path.join(self.base_directory, destination)
        
        if not (self.is_safe_path(source_path) and self.is_safe_path(dest_path)):
            await interaction.response.send_message("Access to one or both paths is not allowed.", ephemeral=True)
            return
            
        try:
            shutil.move(source_path, dest_path)
            await interaction.response.send_message(f"File moved successfully from {source} to {destination}", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FileManager(bot))
