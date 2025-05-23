import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from asyncio import timeout

class AutoPublish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_publish_channels = set()
        self.is_publishing = False
        self.data_file = '.json/autopublish_channels.json'
        self.load_channels()
        self.cleanup_task.start()
        # Add rate limit tracking
        self.last_publish = {}  # Track last publish time per channel
        self.publish_cooldown = 60  # C

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
        if not isinstance(message.channel, discord.TextChannel):
            return

        if message.channel.id not in self.auto_publish_channels:
            return

        # Check cooldown
        current_time = discord.utils.utcnow().timestamp()
        last_publish_time = self.last_publish.get(message.channel.id, 0)
        
        if current_time - last_publish_time < self.publish_cooldown:
            # Still in cooldown period, skip publishing
            return

        try:
            # Verify message still exists and isn't already crossposted
            try:
                message = await message.channel.fetch_message(message.id)
                
                # Check if message is already crossposted or has the publish reaction
                if message.flags.crossposted or "📢" in [r.emoji for r in message.reactions]:
                    return
                    
            except discord.NotFound:
                return
            except Exception as e:
                print(f"Error fetching message: {e}")
                return

            # Implement exponential backoff
            for attempt in range(3):
                try:
                    await message.publish()
                    await message.add_reaction("📢")
                    self.last_publish[message.channel.id] = current_time
                    break
                except discord.HTTPException as e:
                    if e.code == 429:  # Rate limit error
                        retry_after = e.retry_after if hasattr(e, 'retry_after') else (2 ** attempt) * 5
                        print(f"Rate limited in channel {message.channel.id}. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        print(f"HTTP Exception: {e.status} - {e.text}")
                        break
                except discord.Forbidden:
                    print(f"Forbidden: Cannot publish in channel {message.channel.id}")
                    self.auto_publish_channels.remove(message.channel.id)
                    self.save_channels()
                    break
                except Exception as e:
                    print(f"Unexpected error: {type(e).__name__}: {e}")
                    break

        except Exception as e:
            print(f"Error in publish handler: {e}")



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


    @tasks.loop(minutes=5)
    async def cleanup_task(self):

        try:
            total_deleted = 0
            channels_checked = 0
            channels_skipped = 0

            for guild in self.bot.guilds:

                
                try:
                    for channel in guild.text_channels:
                        try:
                            # Check permissions
                            perms = channel.permissions_for(guild.me)
                            if not all([perms.manage_messages, perms.manage_webhooks, perms.read_messages]):
                                continue

                            # Check for webhooks (followed channels)
                            webhooks = await channel.webhooks()
                            followed_channels = [w for w in webhooks if w.type == discord.WebhookType.channel_follower]
                            
                            if followed_channels:
                                channels_checked += 1
                                
                                async with timeout(30):
                                    async for message in channel.history(limit=100):
                                        try:
                                            if "[original message deleted]" in message.content.lower():

                                                await message.delete()
                                                total_deleted += 1

                                                await asyncio.sleep(1.5)
                                        except Exception as msg_e:
                                            print(f"❌ Error deleting message: {str(msg_e)}")
                                            
                        except asyncio.TimeoutError:
                            channels_skipped += 1
                        except Exception as chan_e:
                            channels_skipped += 1
                        
                except Exception as guild_e:
                    print(f"❌ Error processing guild {guild.name}: {str(guild_e)}")
                    



        except Exception as e:
            print(f"\n❌ Major error in cleanup task: {str(e)}")








    @cleanup_task.before_loop
    async def before_cleanup(self):
        # Wait for the bot to be ready before starting the task
        await asyncio.sleep(10)
        await self.bot.wait_until_ready()


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
