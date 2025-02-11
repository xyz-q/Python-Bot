import os
import shutil
from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from typing import List
class FileManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_directory = os.getenv('Media_Storage', '/home/user/Media_Storage')  # Replace with your path

    def is_safe_path(self, path):
        try:
            real_path = os.path.realpath(path)
            return os.path.commonpath([real_path, self.base_directory]) == self.base_directory
        except ValueError:
            return False

    async def file_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete function for file paths"""
        choices = []
        try:
            # Split the current input into directory and partial filename
            current_dir = os.path.dirname(current) if current else ""
            search_dir = os.path.join(self.base_directory, current_dir)
            
            if os.path.isdir(search_dir) and self.is_safe_path(search_dir):
                files = os.listdir(search_dir)
                for file in files:
                    full_path = os.path.join(current_dir, file)
                    if len(full_path.strip()) > 0:  # Ensure path is not empty
                        # Add trailing slash for directories
                        if os.path.isdir(os.path.join(self.base_directory, full_path)):
                            full_path += "/"
                        choices.append(app_commands.Choice(name=full_path, value=full_path))
                
        except Exception as e:
            print(f"Autocomplete error: {e}")
            
        return choices[:25]

    @app_commands.command(name="listfiles", description="List files in a directory")
    @app_commands.autocomplete(path=file_autocomplete)  # This 'path' needs to match the parameter name
    async def list_files(self, interaction: discord.Interaction, path: str = ""):  # This parameter is also 'path'
        """List files in the specified directory"""
        # Defer the response immediately
        await interaction.response.defer(ephemeral=True)
        
        full_path = os.path.join(self.base_directory, path)
        
        if not self.is_safe_path(full_path):
            await interaction.followup.send("Access to this path is not allowed.", ephemeral=True)
            return
            
        try:
            files = os.listdir(full_path)
            if not files:
                await interaction.followup.send("Directory is empty.", ephemeral=True)
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
            
            # Send as followup since we deferred
            await interaction.followup.send(file_list, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="downloadfile", description="Download a file")
    @app_commands.autocomplete(filepath=file_autocomplete)  # This 'filepath' needs to match the parameter name
    async def download_file(self, interaction: discord.Interaction, filepath: str):
        """Download a file from the server"""
        await interaction.response.defer(ephemeral=True)
        
        full_path = os.path.join(self.base_directory, filepath)
        
        if not self.is_safe_path(full_path):
            await interaction.followup.send("Access to this file is not allowed.", ephemeral=True)
            return
            
        try:
            if not os.path.isfile(full_path):
                await interaction.followup.send("File not found.", ephemeral=True)
                return
            
            # Check file size
            file_size = os.path.getsize(full_path)
            if file_size > 8 * 1024 * 1024:  # 8MB limit for Discord
                await interaction.followup.send("File is too large to download (>8MB).", ephemeral=True)
                return
                
            file = discord.File(full_path)
            await interaction.followup.send(file=file, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="deletefile", description="Delete a file")
    @app_commands.autocomplete(filepath=file_autocomplete)  # This 'filepath' needs to match the parameter name
    async def delete_file(self, interaction: discord.Interaction, filepath: str):  # This parameter is also 'filepath'
        """Delete a file from the server"""
        await interaction.response.defer(ephemeral=True)
        
        full_path = os.path.join(self.base_directory, filepath)
        
        if not self.is_safe_path(full_path):
            await interaction.followup.send("Access to this file is not allowed.", ephemeral=True)
            return
            
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
                await interaction.followup.send(f"File {filepath} deleted successfully.", ephemeral=True)
            else:
                await interaction.followup.send("File not found.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="movefile", description="Move a file to another location")
    @app_commands.autocomplete(source=file_autocomplete)  # These parameter names need to match
    @app_commands.autocomplete(destination=file_autocomplete)
    async def move_file(self, interaction: discord.Interaction, source: str, destination: str):  # These parameters also match
        """Move a file to another location"""
        await interaction.response.defer(ephemeral=True)
        
        source_path = os.path.join(self.base_directory, source)
        dest_path = os.path.join(self.base_directory, destination)
        
        if not (self.is_safe_path(source_path) and self.is_safe_path(dest_path)):
            await interaction.followup.send("Access to one or both paths is not allowed.", ephemeral=True)
            return
            
        try:
            shutil.move(source_path, dest_path)
            await interaction.followup.send(
                f"File moved successfully from {source} to {destination}", 
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


# Add this to your code temporarily to debug
    @app_commands.command(name="whoami", description="Check bot permissions")
    async def check_perms(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            current_user = os.getuid()
            current_username = os.getlogin()
            result = f"Running as:\nUID: {current_user}\nUsername: {current_username}"
            await interaction.followup.send(result, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="searchfile", description="Search for a file by name")
    async def search_file(self, interaction: discord.Interaction, filename: str):
        """Search for a file in the directory and subdirectories"""
        await interaction.response.defer(ephemeral=True)
        
        matches = []
        try:
            # Walk through all directories under base_directory
            for root, dirs, files in os.walk(self.base_directory):
                for file in files:
                    if filename.lower() in file.lower():  # Case-insensitive search
                        # Get the relative path from base_directory
                        rel_path = os.path.relpath(os.path.join(root, file), self.base_directory)
                        matches.append(rel_path)
            
            if matches:
                response = "Found these files:\n```"
                for match in matches:
                    response += f"{match}\n"
                response += "```"
            else:
                response = f"No files found matching '{filename}'"
                
            await interaction.followup.send(response, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Error while searching: {str(e)}", ephemeral=True)


    @list_files.error
    @download_file.error
    @delete_file.error
    @move_file.error
    async def on_command_error(self, interaction: discord.Interaction, error):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"An error occurred: {str(error)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FileManager(bot))
