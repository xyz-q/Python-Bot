import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Embed
import cv2
import asyncio
import datetime
import os
from pathlib import Path
import traceback

class DataManager:
    def __init__(self):
        self.recordings_dir = Path("logs/recordings")  # Updated path
        self.snapshots_dir = Path("logs/snapshots")    # Updated path
        self.compressed_dir = Path("logs/compressed")   # Updated path
        self.max_age_days = 30  # Keep uncompressed data for 30 days
        self.compression_schedule_hours = 24  # Compress every 24 hours
        
        # Create directories
        for directory in [self.recordings_dir, self.snapshots_dir, self.compressed_dir]:
            directory.mkdir(parents=True, exist_ok=True)  # Added parents=True
            
        self.compression_task = None
        print("DataManager initialized with directories:")
        print(f"Recordings: {self.recordings_dir}")
        print(f"Snapshots: {self.snapshots_dir}")
        print(f"Compressed: {self.compressed_dir}")

    async def start_compression_schedule(self):
        """Start the scheduled compression task"""
        if self.compression_task is None:
            self.compression_task = asyncio.create_task(self._compression_schedule())
            print("Started compression schedule")

    async def _compression_schedule(self):
        """Run compression periodically"""
        while True:
            try:
                await self.compress_old_data()
                await asyncio.sleep(self.compression_schedule_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                print(f"Error in compression schedule: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    def get_storage_stats(self):
        """Get storage statistics"""
        stats = {
            'logs/recordings': {'count': 0, 'size': 0},
            'logs/snapshots': {'count': 0, 'size': 0},
            'logs/compressed': {'count': 0, 'size': 0}
        }
        
        for directory, key in [
            (self.recordings_dir, 'logs/recordings'),
            (self.snapshots_dir, 'logs/snapshots'),
            (self.compressed_dir, 'logs/compressed')
        ]:
            try:
                files = list(directory.glob('*.*'))
                stats[key]['count'] = len(files)
                stats[key]['size'] = sum(f.stat().st_size for f in files)
            except Exception as e:
                print(f"Error getting stats for {key}: {e}")
                traceback.print_exc()  # Added full traceback
        
        return stats

    async def compress_old_data(self):
        """Compress data older than max_age_days"""
        print("\nStarting compression of old data...")
        current_time = datetime.datetime.now()
        files_processed = 0
        
        # Check videos
        print("\nChecking videos...")
        video_files = list(self.recordings_dir.glob("*.mp4"))
        print(f"Found {len(video_files)} video files")
        
        for video_file in video_files:
            try:
                file_age = current_time - datetime.datetime.fromtimestamp(video_file.stat().st_mtime)
                print(f"\nChecking video: {video_file.name} (Age: {file_age.days} days)")
                
                if file_age.days >= self.max_age_days:
                    print(f"Compressing video: {video_file.name}")
                    await self.compress_video(video_file)
                    files_processed += 1
                else:
                    print(f"Video too recent to compress ({file_age.days} days old)")
                    
            except Exception as e:
                print(f"Error processing video {video_file}: {e}")
                traceback.print_exc()

        # Check images
        print("\nChecking images...")
        image_files = list(self.snapshots_dir.glob("*.jpg"))
        print(f"Found {len(image_files)} image files")
        
        for image_file in image_files:
            try:
                file_age = current_time - datetime.datetime.fromtimestamp(image_file.stat().st_mtime)
                print(f"\nChecking image: {image_file.name} (Age: {file_age.days} days)")
                
                if file_age.days >= self.max_age_days:
                    print(f"Compressing image: {image_file.name}")
                    await self.compress_image(image_file)
                    files_processed += 1
                else:
                    print(f"Image too recent to compress ({file_age.days} days old)")
                    
            except Exception as e:
                print(f"Error processing image {image_file}: {e}")
                traceback.print_exc()

        print(f"\nCompression complete. Processed {files_processed} files.")
        
        # Print storage stats
        stats = self.get_storage_stats()
        print("\nStorage Statistics:")
        for key, data in stats.items():
            size_mb = data['size'] / (1024 * 1024)
            print(f"{key}: {data['count']} files, {size_mb:.1f}MB")
class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.scan_cameras()

    def get_windows_camera_names(self):
        try:
            import subprocess
            # More specific PowerShell command to get camera names
            cmd = """
            Get-PnpDevice | 
            Where-Object { $_.Class -eq 'Image' -or $_.Class -eq 'Camera' } |
            Select-Object FriendlyName |
            Format-List
            """
            output = subprocess.check_output(['powershell', '-Command', cmd], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            cameras = []
            for line in output.split('\n'):
                if line.startswith('FriendlyName'):
                    name = line.split(':', 1)[1].strip()
                    if name and 'Remote' not in name:  # Filter out Remote Desktop cameras
                        cameras.append(name)
            
            # If no cameras found, try alternative method
            if not cameras:
                cmd2 = """
                Get-WmiObject Win32_PnPEntity | 
                Where-Object { $_.PNPClass -eq 'Image' -or $_.PNPClass -eq 'Camera' } |
                Select-Object Name |
                Format-List
                """
                output = subprocess.check_output(['powershell', '-Command', cmd2], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                for line in output.split('\n'):
                    if line.startswith('Name'):
                        name = line.split(':', 1)[1].strip()
                        if name and 'Remote' not in name:
                            cameras.append(name)
            
            print(f"Detected cameras: {cameras}")  # Debug print
            return cameras
        except Exception as e:
            print(f"Error getting camera names: {e}")
            return []

    def scan_cameras(self):
        device_names = self.get_windows_camera_names()
        print(f"Found device names: {device_names}")  # Debug print
        
        for port in range(6):
            try:
                cap = cv2.VideoCapture(port, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Get properties safely
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                        fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)  # Default to 30 if not available
                        
                        # Get name from device list or use default
                        name = device_names[port] if port < len(device_names) else f"Camera {port}"
                        
                        self.cameras[port] = {
                            'name': name,
                            'working': True,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'port': port
                        }
                        print(f"Successfully initialized camera {port}: {name} ({width}x{height} @ {fps}fps)")
                    cap.release()
                else:
                    print(f"Could not open camera {port}")
            except Exception as e:
                print(f"Error scanning camera {port}: {e}")
                traceback.print_exc()  # This will print the full error trace


    def get_camera_name(self, port):
        if port in self.cameras:
            return self.cameras[port]['name']
        return f"USB Camera {port}"

    def is_camera_working(self, port):
        return port in self.cameras and self.cameras[port]['working']

    def get_camera_info(self, port):
        return self.cameras.get(port, None)

class CameraSelectView(ui.View):
    def __init__(self, cog, original_view):
        super().__init__(timeout=None)
        self.cog = cog
        self.original_view = original_view
        self.add_camera_buttons()

    def add_camera_buttons(self):
        # Clear any existing buttons first
        self.clear_items()
        
        # Add camera buttons
        for port in range(6):
            working = self.cog.camera_manager.is_camera_working(port)
            camera_name = self.cog.camera_manager.get_camera_name(port)
            
            if working:  # Only add buttons for working cameras
                button = ui.Button(
                    label=f"📸 {camera_name}",
                    custom_id=f"camera_{port}",
                    style=ButtonStyle.green if port == self.original_view.selected_camera else ButtonStyle.grey,
                    row=port // 2  # Two buttons per row
                )
                button.callback = self.create_camera_callback(port)
                self.add_item(button)

        # Add back button at the bottom
        back_button = ui.Button(
            label="↩️ Back",
            style=ButtonStyle.blurple,
            custom_id="back_to_security",
            row=3  # Put back button on the last row
        )
        back_button.callback = self.back_to_security
        self.add_item(back_button)

    def create_camera_callback(self, camera_port):
        async def camera_callback(interaction: discord.Interaction):
            try:
                self.original_view.selected_camera = camera_port
                camera_name = self.cog.camera_manager.get_camera_name(camera_port)
                

                
                # Update the main security view
                embed = self.original_view.create_status_embed()
                await interaction.message.edit(embed=embed, view=self.original_view)
                
            except Exception as e:
                print(f"Error in camera callback: {e}")
                traceback.print_exc()
                await interaction.response.send_message(
                    f"❌ Error selecting camera: {str(e)}", 
                    ephemeral=True,
                    delete_after=120
                )
            
        return camera_callback

    async def back_to_security(self, interaction: discord.Interaction):
        embed = self.original_view.create_status_embed()
        await interaction.response.edit_message(embed=embed, view=self.original_view)

    def create_camera_embed(self):
        embed = Embed(title="Camera Selection", color=discord.Color.blue())
        embed.description = "Select a camera to use for security monitoring"
        
        for port in range(6):
            camera_info = self.cog.camera_manager.get_camera_info(port)
            if camera_info:
                embed.add_field(
                    name=f"📸 {camera_info['name']}",
                    value=f"Port: {port}\n"
                          f"Resolution: {camera_info['width']}x{camera_info['height']}\n"
                          f"FPS: {camera_info['fps']}\n"
                          f"Status: ✅ Available",
                    inline=True
                )
            else:
                embed.add_field(
                    name=f"📸 Camera {port}",
                    value=f"Port: {port}\nStatus: ❌ Not Available",
                    inline=True
                )

        embed.set_footer(text="Click a button below to select a camera")
        return embed

class SecurityView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.armed = False
        self.recording = False
        self.selected_camera = 0
        self.recording_task = None
        self.add_default_buttons()
        
        # Create directories
        self.recordings_dir = Path("logs/recordings")
        self.snapshots_dir = Path("logs/snapshots")
        self.recordings_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)
        print("SecurityView initialized")

    def add_default_buttons(self):
        # Existing buttons
        arm_button = ui.Button(
            label="🔴 DISARMED",
            style=ButtonStyle.red,
            custom_id="security_arm"
        )
        arm_button.callback = self.arm_callback
        self.add_item(arm_button)

        camera_button = ui.Button(
            label="🎥 Cameras",
            style=ButtonStyle.blurple,
            custom_id="camera_select"
        )
        camera_button.callback = self.camera_callback
        self.add_item(camera_button)

        # New capture button
        capture_button = ui.Button(
            label="📸 Capture",
            style=ButtonStyle.green,
            custom_id="capture_photo"
        )
        capture_button.callback = self.capture_callback
        self.add_item(capture_button)

        settings_button = ui.Button(
            label="⚙️ Settings",
            style=ButtonStyle.gray,
            custom_id="security_settings"
        )
        settings_button.callback = self.settings_callback
        self.add_item(settings_button)

    async def capture_callback(self, interaction: discord.Interaction):
        print(f"Capturing photo from camera {self.selected_camera}")
        try:
            # Initialize camera
            cap = cv2.VideoCapture(self.selected_camera, cv2.CAP_DSHOW)
            if not cap.isOpened():
                await interaction.response.send_message(
                    f"❌ Failed to open camera {self.selected_camera}!", 
                    ephemeral=True,
                    delete_after=120
                )
                return

            # Try to capture frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                await interaction.response.send_message(
                    "❌ Failed to capture image!", 
                    ephemeral=True,
                    delete_after=120
                )
                return

            # Save image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.snapshots_dir / f"snapshot_{timestamp}.jpg"
            cv2.imwrite(str(filename), frame)

            # Create embed with image
            embed = discord.Embed(
                title="📸 Camera Snapshot",
                description=f"Captured from {self.cog.camera_manager.get_camera_name(self.selected_camera)}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Details",
                value=f"📅 Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"📁 File: {filename.name}\n"
                      f"📏 Size: {frame.shape[1]}x{frame.shape[0]}"
            )
            
            # Send the image
            file = discord.File(str(filename), filename=filename.name)
            await interaction.response.send_message(
                embed=embed,
                file=file,
                ephemeral=True,
                delete_after=120# Set to True if you want only the user to see it
            )

            print(f"Snapshot saved: {filename}")

        except Exception as e:
            print(f"Error capturing photo: {e}")
            traceback.print_exc()
            await interaction.response.send_message(
                f"❌ Error capturing photo: {str(e)}", 
                ephemeral=True,
                delete_after=120
            )

    def create_status_embed(self):
        embed = Embed(title="Security Control Panel", color=discord.Color.blue())
        
        # System Status
        status_text = "🟢 ARMED" if self.armed else "🔴 DISARMED"
        if self.recording:
            status_text += "\n⏺️ Recording Active"
        embed.add_field(name="System Status", value=status_text, inline=False)
        
        # Camera Info
        camera_name = self.cog.camera_manager.get_camera_name(self.selected_camera)
        camera_info = self.cog.camera_manager.get_camera_info(self.selected_camera)
        if camera_info:
            camera_text = (
                f"📸 {camera_name}\n"
                f"Resolution: {camera_info['width']}x{camera_info['height']}\n"
                f"FPS: {camera_info['fps']}"
            )
        else:
            camera_text = f"📸 {camera_name}"
        embed.add_field(name="Selected Camera", value=camera_text, inline=True)
        
        # Recording Info
        if self.recording:
            try:
                files = list(self.recordings_dir.glob("recording_*.mp4"))
                if files:
                    latest = max(files, key=os.path.getctime)
                    size = os.path.getsize(latest) / (1024 * 1024)
                    recording_text = (
                        f"Current File: {latest.name}\n"
                        f"Size: {size:.1f}MB"
                    )
                else:
                    recording_text = "Starting recording..."
            except Exception as e:
                recording_text = f"Recording... (Error reading file info: {e})"
        else:
            recording_text = "⏹️ Not Recording"
        
        embed.add_field(name="Recording Status", value=recording_text, inline=True)
        
        # Latest Snapshot Info
        try:
            snapshot_files = list(self.snapshots_dir.glob("snapshot_*.jpg"))
            if snapshot_files:
                latest = max(snapshot_files, key=os.path.getctime)
                size = os.path.getsize(latest) / (1024 * 1024)
                snapshot_text = (
                    f"Latest: {latest.name}\n"
                    f"Size: {size:.1f}MB"
                )
            else:
                snapshot_text = "No snapshots taken"
        except Exception as e:
            snapshot_text = f"Error reading snapshots: {e}"
        
        embed.add_field(name="Latest Snapshot", value=snapshot_text, inline=True)
        
        # Storage Info
        try:
            total_recordings = sum(f.stat().st_size for f in self.recordings_dir.glob("**/*"))
            total_snapshots = sum(f.stat().st_size for f in self.snapshots_dir.glob("**/*"))
            storage_text = (
                f"💾 Recordings: {total_recordings / (1024 * 1024):.1f}MB\n"
                f"📸 Snapshots: {total_snapshots / (1024 * 1024):.1f}MB\n"
                f"📊 Total: {(total_recordings + total_snapshots) / (1024 * 1024):.1f}MB"
            )
            embed.add_field(name="Storage", value=storage_text, inline=True)
        except Exception as e:
            embed.add_field(name="Storage", value=f"Error: {e}", inline=True)
        
        embed.set_footer(text=f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    async def arm_callback(self, interaction: discord.Interaction):
        print(f"Arm button pressed. Current armed status: {self.armed}")  # Debug print
        try:
            button = [x for x in self.children if x.custom_id == "security_arm"][0]
            self.armed = not self.armed
            
            if self.armed:
                print("System armed, starting recording...")  # Debug print
                # First respond to the interaction
                await interaction.response.defer()
                
                # Start recording
                self.recording = True
                # Create and start the recording task
                self.recording_task = asyncio.create_task(self.record_video(interaction))
                print(f"Recording task created: {self.recording_task}")  # Debug print
                
                button.label = "🟢 ARMED"
                button.style = ButtonStyle.green
                

            else:
                print("System disarmed, stopping recording...")  # Debug print
                self.recording = False
                if self.recording_task:
                    print("Cancelling recording task...")  # Debug print
                    self.recording_task.cancel()
                    self.recording_task = None
                
                button.label = "🔴 DISARMED"
                button.style = ButtonStyle.red
                

            
            # Update embed
            embed = self.create_status_embed()
            await interaction.message.edit(embed=embed, view=self)
            
        except Exception as e:
            print(f"Error in arm_callback: {e}")  # Debug print
            traceback.print_exc()  # Print full error traceback
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True, delete_after=120)

    async def camera_callback(self, interaction: discord.Interaction):
        try:
            camera_view = CameraSelectView(self.cog, self)
            embed = camera_view.create_camera_embed()
            await interaction.response.edit_message(embed=embed, view=camera_view)
        except Exception as e:
            print(f"Error in camera button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(
                f"❌ Error opening camera selection: {str(e)}", 
                ephemeral=True,
                delete_after=120
            )

    async def settings_callback(self, interaction: discord.Interaction):
        # Your settings logic here
        pass

    async def record_video(self, interaction):
        print(f"Starting recording with camera {self.selected_camera}")  # Debug print
        try:
            # Initialize camera
            cap = cv2.VideoCapture(self.selected_camera, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print(f"Failed to open camera {self.selected_camera}")
                await interaction.followup.send(f"❌ Failed to open camera {self.selected_camera}!", ephemeral=True, delete_after=120)
                self.recording = False
                return

            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"Camera initialized: {width}x{height} @ {fps}fps")

            # Try different codecs
            codecs = [
                ('mp4v', '.mp4'),
                ('XVID', '.avi'),
                ('MJPG', '.avi'),
                ('X264', '.mp4')
            ]
            
            out = None
            filename = None
            
            for codec, ext in codecs:
                try:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = self.recordings_dir / f"recording_{timestamp}{ext}"
                    print(f"Trying codec {codec} with file {filename}")
                    
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    out = cv2.VideoWriter(
                        str(filename), 
                        fourcc, 
                        30.0,  # Force 30 FPS
                        (width, height)
                    )
                    
                    if out is not None and out.isOpened():
                        print(f"Successfully created video writer with codec {codec}")
                        break
                    else:
                        print(f"Failed with codec {codec}")
                        if out is not None:
                            out.release()
                        
                except Exception as e:
                    print(f"Error with codec {codec}: {e}")
                    if out is not None:
                        out.release()
                    continue
            
            if out is None or not out.isOpened():
                print("Failed to create video writer with any codec")
                await interaction.followup.send("❌ Failed to create video file!", ephemeral=True, delete_after=120)
                self.recording = False
                return

            frames_written = 0
            start_time = datetime.datetime.now()
            print("Starting frame capture loop")  # Debug print

            while self.recording:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame")
                    break

                # Write frame
                out.write(frame)
                frames_written += 1

                if frames_written % 100 == 0:  # Print every 100 frames
                    print(f"Frames written: {frames_written}")

                # Create new file every hour
                if (datetime.datetime.now() - start_time).seconds >= 3600:
                    break

                # Small delay to prevent CPU overload
                await asyncio.sleep(0.001)

            # Clean up
            if out is not None:
                out.release()
            cap.release()

            if frames_written > 0 and filename is not None:
                file_size = os.path.getsize(filename) / (1024 * 1024)
                print(f"Saved recording: {filename} ({file_size:.1f}MB, {frames_written} frames)")
                await interaction.channel.send(
                    f"💾 Saved recording: {filename.name}\n"
                    f"📊 Size: {file_size:.1f}MB\n"
                    f"🎞️ Frames: {frames_written}"
                )
            else:
                print(f"No frames written, removing empty file: {filename}")
                if filename and filename.exists():
                    os.remove(filename)

        except asyncio.CancelledError:
            print("Recording cancelled")
            if 'out' in locals() and out is not None:
                out.release()
            if 'cap' in locals() and cap is not None:
                cap.release()
            raise

        except Exception as e:
            print(f"Unexpected error in record_video: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Recording error: {str(e)}", ephemeral=True, delete_after=120)
            self.recording = False
            if 'out' in locals() and out is not None:
                out.release()
            if 'cap' in locals() and cap is not None:
                cap.release()

        print("Recording stopped normally")



class SecurityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.camera_manager = CameraManager()
        self.data_manager = DataManager()
        self.security_view = SecurityView(self)
        self.control_message = None

    async def cog_load(self):
        """Called when the cog is loaded"""
        await self.data_manager.start_compression_schedule()

    @commands.command(name="compress")
    @commands.is_owner()
    async def force_compress(self, ctx):
        """Force compression of old data"""
        await ctx.message.delete()
        await self.data_manager.compress_old_data()
        await ctx.send("✅ Compression completed!", delete_after=5)
 # Store the control panel message

    @commands.command(name="security")
    @commands.is_owner()
    async def security_panel(self, ctx):
        """Display the security control panel"""
        # Delete the old control panel if it exists
        if self.control_message:
            try:
                await self.control_message.delete()
            except:
                pass

        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass

        # Send all messages in the channel to push the embed to bottom
        async for message in ctx.channel.history(limit=None):
            try:
                await message.delete()
            except:
                continue

        # Create and send the new control panel
        embed = self.security_view.create_status_embed()
        self.control_message = await ctx.send(embed=embed, view=self.security_view)

        # Pin the message to keep it easily accessible
        try:
            await self.control_message.pin()
        except:
            pass

async def setup(bot):
    await bot.add_cog(SecurityCommands(bot))
