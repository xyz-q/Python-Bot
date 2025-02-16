import discord
from discord.ext import commands, tasks
import urllib.request
from io import BytesIO
from PIL import Image
import asyncio
import requests
import time

class SecurityCamera(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url = "http://192.168.0.163:5000/stream/video_feed"
        self.update_interval = 10  # seconds between updates
        self.error_update_interval = 17  # seconds between error message updates
        self.channel_id = 1340119207513427999
        self.message = None
        self.message_id = None
        self.is_running = True
        self.last_error_message = None
        self.last_error_update = 0
        self.run_camera_feed.start()

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
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Error deleting message: {e}")

            # Try to fetch existing message
            if self.message_id:
                try:
                    self.message = await channel.fetch_message(self.message_id)
                    return self.message
                except:
                    self.message = None
                    self.message_id = None

            # Create new message if we don't have one
            if self.message is None:
                embed = discord.Embed(
                    title="Security Camera",
                    description="🎥 Starting camera feed...",
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Stream updates every 5 seconds")
                self.message = await channel.send(embed=embed)
                self.message_id = self.message.id
                print(f"Created new message with ID: {self.message_id}")

            return self.message

        except Exception as e:
            print(f"Error getting/creating message: {e}")
            return None

    async def update_error_message(self, error_type="connection", force_update=False):
        """Updates the embed with an error message"""
        current_time = time.time()
        
        # Only update if it's a new error type or enough time has passed
        if (self.last_error_message != error_type or 
            force_update or 
            current_time - self.last_error_update >= self.error_update_interval):
            
            try:
                message = await self.get_or_create_message()
                if message:
                    embed = discord.Embed(
                        title="Security Camera",
                        description="❌ Camera Offline",
                        color=discord.Color.red()
                    )
                    
                    if error_type == "connection":
                        status_text = "Cannot connect to camera server"
                    else:
                        status_text = "Unknown error occurred"
                        
                    embed.add_field(name="Status", value=status_text, inline=False)
                    embed.add_field(name="Last Check", value=discord.utils.format_dt(discord.utils.utcnow(), 'R'), inline=False)
                    embed.set_footer(text="Will automatically reconnect when camera is available")
                    
                    await message.edit(embed=embed)
                    await message.edit(attachments=[])
                    
                    self.last_error_message = error_type
                    self.last_error_update = current_time
            except Exception as e:
                print(f"Error updating error message: {e}")

    @tasks.loop(seconds=10)
    async def run_camera_feed(self):
        """Runs the continuous camera feed"""
        try:
            # Try to connect to the stream
            response = requests.get(self.url, stream=True, timeout=5)
            if response.status_code != 200:
                await self.update_error_message()
                return

            bytes_data = b''
            frame_count = 0
            update_count = 0
            last_update_time = time.time()
            self.last_error_message = None  # Reset error message state when connected

            for chunk in response.iter_content(chunk_size=1024):
                if not self.is_running:
                    return

                if not chunk:
                    continue

                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')

                if a != -1 and b != -1:
                    try:
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]

                        frame_count += 1
                        current_time = time.time()

                        if current_time - last_update_time >= self.update_interval:
                            message = await self.get_or_create_message()
                            if message is None:
                                continue

                            image = Image.open(BytesIO(jpg))
                            img_buffer = BytesIO()
                            image.save(img_buffer, format='PNG')
                            img_buffer.seek(0)

                            embed = discord.Embed(
                                title="Security Camera",
                                description="🎥 Live View",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="Status", value="Connected", inline=True)
                            embed.add_field(name="Updates", value=str(update_count), inline=True)
                            embed.add_field(name="Total Frames", value=str(frame_count), inline=True)
                            embed.set_image(url="attachment://view.png")
                            embed.set_footer(text="Stream updates every 5 seconds")
                            embed.timestamp = discord.utils.utcnow()

                            await message.edit(embed=embed)
                            await message.edit(attachments=[discord.File(img_buffer, 'view.png')])
                            update_count += 1
                            last_update_time = current_time

                    except Exception as frame_error:
                        print(f"Frame processing error: {frame_error}")
                        continue

        except requests.exceptions.RequestException as e:
            await self.update_error_message("connection", force_update=False)
        except Exception as e:
            print(f"Stream error: {e}")
            await self.update_error_message("unknown", force_update=False)

    @run_camera_feed.before_loop
    async def before_camera_feed(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def reset_camera(self, ctx):
        """Resets the camera feed message"""
        self.message = None
        self.message_id = None
        self.last_error_message = None
        self.last_error_update = 0
        await ctx.send("Camera feed message reset. A new message will be created on next update.")

async def setup(bot):
    await bot.add_cog(SecurityCamera(bot))
