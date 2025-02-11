import os
import shutil
from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from typing import List
from datetime import datetime, timedelta


def owner_only():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != 110927272210354176:
            await interaction.response.send_message("⛔ You are not authorized to use this command.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)
class FileManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_directory = os.getenv('Media_Storage', '/home/user/Media_Storage')  # Replace with your path
        self.waiting_for_upload = {} 
        self.owner_id = bot.owner_id
        
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



  # Store user IDs and their upload states


    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle file uploads and cancellation"""
        # Ignore bot messages
        if message.author.bot:
            return

        user_id = message.author.id
        
      t

        
        # Check if user is in upload mode
        if user_id not in self.waiting_for_upload:
            return
            
        upload_state = self.waiting_for_upload[user_id]
        
        # Debug print


        # If message has no attachments, cancel upload
        if not message.attachments:
            del self.waiting_for_upload[user_id]
            embed = discord.Embed(
                title="File Upload Cancelled",
                description="Upload mode has been cancelled.",
                color=discord.Color.red()
            )
            try:
                channel = message.channel
                original_msg = await channel.fetch_message(upload_state['message_id'])
                await original_msg.edit(embed=embed)
            except Exception as e:
                print(f"Error editing message: {e}")
                await message.reply(embed=embed)
            return

        # Process file upload
        for attachment in message.attachments:
            try:

                # Create full file path
                file_path = os.path.join(upload_state['path'], attachment.filename)

                
                # Download and save the file
                await attachment.save(file_path)
                
                embed = discord.Embed(
                    title="File Upload Success",
                    description=f"File `{attachment.filename}` has been uploaded successfully!",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Location",
                    value=f"```{os.path.relpath(file_path, self.base_directory)}```",
                    inline=False
                )
                
            except Exception as e:
                print(f"Error saving file: {e}")
                embed = discord.Embed(
                    title="File Upload Failed",
                    description=f"Error: {str(e)}",
                    color=discord.Color.red()
                )

            try:
                channel = message.channel
                original_msg = await channel.fetch_message(upload_state['message_id'])
                await original_msg.edit(embed=embed)
            except Exception as e:
                print(f"Error editing message: {e}")
                await message.reply(embed=embed)

        # Remove upload state
        del self.waiting_for_upload[user_id]

    @owner_only()
    @app_commands.autocomplete(path=file_autocomplete)  # This 'path' needs to match the parameter name
    
    @app_commands.command(name="uploadfile", description="Upload a file to the server")
    async def upload_file(self, interaction: discord.Interaction, path: str = ""):
        """Start the file upload process"""
        try:
            user_id = interaction.user.id

            # Check if user already has an upload in progress
            if user_id in self.waiting_for_upload:
                await interaction.response.send_message("You already have an upload in progress!", ephemeral=True)
                return

            # Validate and create the upload path
            upload_path = os.path.join(self.base_directory, path)
            
            # Check if path is safe


            # Create embed
            embed = discord.Embed(
                title="📤 File Upload Mode",
                description="Upload your file within the next 45 seconds.\nSend any message to cancel.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📂 Upload Location",
                value=f"```{path or 'root directory'}```",
                inline=False
            )
            embed.add_field(
                name="⏳ Time Remaining",
                value="45 seconds",
                inline=False
            )
            embed.set_footer(text="Waiting for file...")

            # Send response
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Get the message for later editing
            msg = await interaction.original_response()

            # Store upload state
            self.waiting_for_upload[user_id] = {
                'path': upload_path,
                'expires': datetime.now() + timedelta(seconds=45),
                'message_id': msg.id,
                'channel_id': interaction.channel_id
            }

            # Start countdown
            for remaining in range(44, -1, -1):
                if user_id not in self.waiting_for_upload:
                    return  # Upload was cancelled
                    
                embed.set_field_at(
                    1,
                    name="⏳ Time Remaining",
                    value=f"{remaining} seconds",
                    inline=False
                )
                
                try:
                    await msg.edit(embed=embed)
                except:
                    pass
                    
                await asyncio.sleep(1)

            # Handle expiration
            if user_id in self.waiting_for_upload:
                del self.waiting_for_upload[user_id]
                embed.description = "⏰ Upload time expired!"
                embed.color = discord.Color.red()
                try:
                    await msg.edit(embed=embed)
                except:
                    pass

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            try:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

    @upload_file.error
    async def upload_file_error(self, interaction: discord.Interaction, error):
        try:
            if isinstance(error, app_commands.errors.CheckFailure):
                await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"❌ An unexpected error occurred: {str(error)}", 
                    ephemeral=True
                )
        except discord.errors.InteractionResponded:
            # If interaction was already responded to, use followup
            await interaction.followup.send(
                "❌ An error occurred while processing the command.", 
                ephemeral=True
            )
        except Exception as e:
            # If we can't respond to the interaction at all
            print(f"Failed to handle error: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ An error occurred while processing the command.", 
                    ephemeral=True
                )
            except:
                pass  # At this point, we can't do anything else


    @owner_only()
    @app_commands.command(name="mkdir", description="Create a new directory")
    @app_commands.autocomplete(path=file_autocomplete)
    async def make_directory(self, interaction: discord.Interaction, name: str, path: str = ""):
        """Create a new directory"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Combine path and name
            full_path = os.path.join(self.base_directory, path, name)
            
            # Check if path is safe
            if not self.is_safe_path(full_path):
                await interaction.followup.send("❌ Access to this path is not allowed.", ephemeral=True)
                return
            
            # Check if directory already exists
            if os.path.exists(full_path):
                await interaction.followup.send("❌ Directory already exists!", ephemeral=True)
                return
            
            # Create directory
            os.makedirs(full_path)
            
            embed = discord.Embed(
                title="📁 Directory Created",
                description=f"Successfully created directory:\n```{os.path.join(path, name)}```",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to create directory: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


    @owner_only()
    @app_commands.command(name="rmdir", description="Remove a directory")
    @app_commands.autocomplete(path=file_autocomplete)
    async def remove_directory(self, interaction: discord.Interaction, path: str, force: bool = False):
        """Remove a directory"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Create full path
            full_path = os.path.join(self.base_directory, path)
            
            # Check if path is safe
            if not self.is_safe_path(full_path):
                await interaction.followup.send("❌ Access to this path is not allowed.", ephemeral=True)
                return
            
            # Check if directory exists
            if not os.path.exists(full_path):
                await interaction.followup.send("❌ Directory does not exist!", ephemeral=True)
                return
            
            # Check if it's actually a directory
            if not os.path.isdir(full_path):
                await interaction.followup.send("❌ The specified path is not a directory!", ephemeral=True)
                return
            
            # Check if directory is empty or force flag is set
            if not force and os.listdir(full_path):
                embed = discord.Embed(
                    title="⚠️ Directory Not Empty",
                    description=(
                        f"Directory contains files or subdirectories.\n"
                        f"Use `/rmdir path:{path} force:True` to remove it and all its contents."
                    ),
                    color=discord.Color.yellow()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Remove directory
            if force:
                shutil.rmtree(full_path)
            else:
                os.rmdir(full_path)
            
            embed = discord.Embed(
                title="🗑️ Directory Removed",
                description=f"Successfully removed directory:\n```{path}```",
                color=discord.Color.green()
            )
            if force:
                embed.set_footer(text="Directory and all its contents were removed")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to remove directory: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


    @make_directory.error
    @remove_directory.error
    async def directory_error(self, interaction: discord.Interaction, error):
        try:
            if isinstance(error, app_commands.errors.CheckFailure):
                await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"❌ An unexpected error occurred: {str(error)}", 
                    ephemeral=True
                )
        except discord.errors.InteractionResponded:
            await interaction.followup.send(
                "❌ An error occurred while processing the command.", 
                ephemeral=True
            )
        except Exception as e:
            print(f"Failed to handle error: {str(e)}")



    @owner_only()
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


    @owner_only()
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


    @owner_only()
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



    @owner_only()
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



    @owner_only()
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

    @owner_only()
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




async def setup(bot):
    await bot.add_cog(FileManager(bot))
