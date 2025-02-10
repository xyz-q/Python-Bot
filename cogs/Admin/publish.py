import discord
from discord.ext import commands, tasks
import json
import os
import asyncio

class AutoPublish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_publish_channels = set()
        self.is_publishing = False
        self.data_file = '.json/autopublish_channels.json'
        self.load_channels()
        self.cleanup_task.start()

    def load_channels(self):
        """Load auto-publish channels from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    channels = json.load(f)
                    self.auto_publish_channels = set(channels)
                    self.is_publishing = bool(self.auto_publish_channels)
        except Exception as e:
            print(f"Error loading auto-publish channels: {e}")
            self.auto_publish_channels = set()

    def save_channels(self):
        """Save auto-publish channels to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(list(self.auto_publish_channels), f)
        except Exception as e:
            print(f"Error saving auto-publish channels: {e}")

    @commands.command()
    @commands.is_owner()
    async def publish(self, ctx):
        """Start auto-publishing messages in the current channel"""
        if not isinstance(ctx.channel, discord.TextChannel) or not ctx.channel.is_news():
            await ctx.send("This command can only be used in announcement channels!")
            return

        if ctx.channel.id in self.auto_publish_channels:
            await ctx.send("Auto-publishing is already enabled in this channel!")
            return

        self.auto_publish_channels.add(ctx.channel.id)
        self.is_publishing = True
        self.save_channels()  # Save the updated channels
        await ctx.send("✅ Auto-publishing enabled for this channel!")

    @commands.command()
    @commands.is_owner()
    async def stoppublish(self, ctx):
        """Stop auto-publishing messages in the current channel"""
        if ctx.channel.id not in self.auto_publish_channels:
            await ctx.send("Auto-publishing is not enabled in this channel!")
            return

        self.auto_publish_channels.remove(ctx.channel.id)
        if not self.auto_publish_channels:
            self.is_publishing = False
        self.save_channels()  # Save the updated channels
        await ctx.send("❌ Auto-publishing disabled for this channel!")

    @commands.command()
    @commands.is_owner()
    async def publishing(self, ctx):
        """Check which channels have auto-publishing enabled"""
        if not self.auto_publish_channels:
            await ctx.send("Auto-publishing is not enabled in any channels!")
            return

        channel_mentions = []
        for channel_id in self.auto_publish_channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                channel_mentions.append(channel.mention)
            else:
                # Remove invalid channels
                self.auto_publish_channels.remove(channel_id)
                self.save_channels()

        if not channel_mentions:
            await ctx.send("Auto-publishing is not enabled in any valid channels!")
            return

        channels_list = "\n".join(channel_mentions)
        await ctx.send(f"Auto-publishing is enabled in the following channels:\n{channels_list}")

    @commands.Cog.listener()
    async def on_message(self, message):
        await asyncio.sleep(2)

        
        if not isinstance(message.channel, discord.TextChannel):

            return

        
        if message.channel.id in self.auto_publish_channels:
            bot_permissions = message.channel.permissions_for(message.guild.me)

            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:

                    
                    # Try to fetch the message first to ensure it exists
                    try:
                        # Refresh message object
                        message = await message.channel.fetch_message(message.id)
                        if message.flags.crossposted:
                            print("Message is already crossposted")
                            break
                    except discord.NotFound:

                        break
                    except Exception as e:
                        print(f"Error fetching message: {e}")
                    
                    # Attempt to publish with shorter timeout
                    try:
                        publish_task = asyncio.create_task(message.publish())
                        await asyncio.wait_for(publish_task, timeout=5.0)

                        await message.add_reaction("📢")

                        break
                        
                    except asyncio.TimeoutError:
                        print(f"Publishing timed out on attempt {retry_count + 1}")
                        # Cancel the publish task if it's still running
                        if not publish_task.done():
                            publish_task.cancel()
                            try:
                                await publish_task
                            except asyncio.CancelledError:
                                print("Publish task cancelled")
                        
                        if retry_count < max_retries - 1:
                            wait_time = (retry_count + 1) * 2

                            await asyncio.sleep(wait_time)
                            retry_count += 1
                            continue
                        else:
                            print("Max retries reached - giving up")
                            # Try one last time with a longer timeout
                            try:

                                await asyncio.wait_for(message.publish(), timeout=30.0)
                                print("Final attempt succeeded!")
                                await message.add_reaction("📢")
                            except:
                                print("Final attempt failed")
                            break
                            
                except discord.Forbidden as e:
                    print(f"Forbidden error: {e}")
                    self.auto_publish_channels.remove(message.channel.id)
                    self.save_channels()
                    print(f"Removed channel {message.channel.id} from auto_publish_channels")
                    break
                    
                except discord.HTTPException as e:
                    print(f"HTTP Exception: {e.status} - {e.text}")
                    if e.code == 429:  # Rate limit error
                        if retry_count < max_retries - 1:
                            wait_time = e.retry_after if hasattr(e, 'retry_after') else 5
                            print(f"Rate limited - waiting {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                            retry_count += 1
                            continue
                        else:
                            print("Max retries reached - giving up")
                            break
                    else:

                        break
                        
                except Exception as e:
                    print(f"Unexpected error: {type(e).__name__}: {e}")
                    break





    @commands.command()
    async def checkpublish(self, ctx):
        """Check publishing configuration for this channel"""
        channel = ctx.channel
        bot_member = ctx.guild.me
        perms = channel.permissions_for(bot_member)
        
        status = {
            "Is Announcement Channel": channel.is_news(),
            "In Publish List": channel.id in self.publish_channels,
            "Bot Permissions": {
                "Manage Messages": perms.manage_messages,
                "View Channel": perms.view_channel,
                "Send Messages": perms.send_messages,
                "Embed Links": perms.embed_links,
                "Add Reactions": perms.add_reactions
            }
        }
        
        embed = discord.Embed(title="Publishing Status Check", color=discord.Color.blue())
        for key, value in status.items():
            if key != "Bot Permissions":
                embed.add_field(name=key, value=str(value), inline=False)
        
        perms_text = "\n".join(f"{k}: {'✅' if v else '❌'}" for k,v in status["Bot Permissions"].items())
        embed.add_field(name="Bot Permissions", value=perms_text, inline=False)
        
        await ctx.send(embed=embed)



    @tasks.loop(minutes=30)
    async def cleanup_task(self):
        try:
            total_deleted = 0
            channels_checked = 0
            channels_skipped = 0

            for guild in self.bot.guilds:
                # Only look at announcement channels
                announcement_channels = [channel for channel in guild.text_channels if channel.is_news()]
                
                for channel in announcement_channels:  # Changed from guild.text_channels
                    try:
                        channels_checked += 1
                        
                        # Rest of your existing channel processing code...
                        # Check bot permissions
                        perms = channel.permissions_for(guild.me)
                        if not perms.manage_messages:
                            channels_skipped += 1
                            continue

                        deleted_count = 0
                        message_count = 0
                        
                        # Add timeout handling for channel history
                        try:
                            async with asyncio.timeout(30):  # 30 second timeout per channel
                                async for message in channel.history(limit=100):
                                    try:
                                        message_count += 1
                                        
                                        if "[Original Message Deleted]" in message.content:
                                            origin_guild = message.guild.name
                                            current_guild = guild.name
                                            

                                            
                                            if (message.flags.crossposted or 
                                                message.reference or 
                                                message.guild.id != guild.id):
                                                try:
                                                    await message.delete()
                                                    deleted_count += 1

                                                    await asyncio.sleep(1.5)  # Increased rate limit delay
                                                except discord.Forbidden:
                                                    print(f"  ✕ Failed to delete - No permission")
                                                except discord.NotFound:
                                                    print(f"  ✕ Failed to delete - Message already gone")
                                                except discord.HTTPException as e:
                                                    print(f"  ⚠ Discord API Error: {e}")
                                                    await asyncio.sleep(5)  # Extra delay on API errors
                                                except Exception as e:
                                                    print(f"  ✕ Error: {type(e).__name__}: {e}")

                                    
                                    except Exception as message_error:
                                        print(f"  ⚠ Error processing message: {type(message_error).__name__}: {message_error}")
                                        continue  # Skip to next message
                        
                        except asyncio.TimeoutError:

                            channels_skipped += 1
                            continue
                        
                        if message_count > 0:

                            total_deleted += deleted_count
                        
                        # Add a small delay between channels
                        await asyncio.sleep(2)
                            
                    except Exception as channel_error:
                        print(f"⚠ Error in channel {channel.name}: {type(channel_error).__name__}: {channel_error}")
                        channels_skipped += 1
                        await asyncio.sleep(5)  # Delay before next channel on error
                        continue

            print(f"\n=== Cleanup Complete ===")
            print(f"Channels checked: {channels_checked}")
            print(f"Channels skipped: {channels_skipped}")
            print(f"Total messages deleted: {total_deleted}")

        except Exception as e:
            print(f"❌ Fatal error in cleanup task: {type(e).__name__}: {e}")

        finally:
            print("=== Task finished ===\n")


    @cleanup_task.before_loop
    async def before_cleanup(self):
        # Wait for the bot to be ready before starting the task
        await self.bot.wait_until_ready()
        print("Cleanup task is ready to start")

    @commands.command()
    @commands.is_owner()
    async def toggle_cleanup(self, ctx):
        """Toggle the automatic cleanup task"""
        if self.cleanup_task.is_running():
            self.cleanup_task.cancel()
            await ctx.send("✅ Automatic cleanup task disabled")
        else:
            self.cleanup_task.start()
            await ctx.send("✅ Automatic cleanup task enabled")

    @commands.command()
    @commands.is_owner()
    async def cleanup_status(self, ctx):
        """Check the status of the cleanup task"""
        if self.cleanup_task.is_running():
            next_run = self.cleanup_task.next_iteration
            if next_run:
                time_until = next_run - discord.utils.utcnow()
                minutes = int(time_until.total_seconds() / 60)
                await ctx.send(f"✅ Cleanup task is running\nNext run in: {minutes} minutes")
            else:
                await ctx.send("✅ Cleanup task is running")
        else:
            await ctx.send("❌ Cleanup task is not running")

    @commands.command()
    @commands.is_owner()
    async def set_cleanup_interval(self, ctx, minutes: int):
        """Set the cleanup task interval (in minutes)"""
        if minutes < 5:
            await ctx.send("❌ Interval must be at least 5 minutes!")
            return
        
        self.cleanup_task.change_interval(minutes=minutes)
        await ctx.send(f"✅ Cleanup interval set to {minutes} minutes")

async def setup(bot):
    await bot.add_cog(AutoPublish(bot))
