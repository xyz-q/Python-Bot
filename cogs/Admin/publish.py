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

        if message.channel.id in self.auto_publish_channels:
            try:
                await message.publish()
                await message.add_reaction("📢")
            except discord.Forbidden:
                # Bot doesn't have permission to publish
                self.auto_publish_channels.remove(message.channel.id)
                self.save_channels()
            except discord.HTTPException:
                # Message failed to publish (e.g., already published)
                pass

async def setup(bot):
    await bot.add_cog(AutoPublish(bot))
