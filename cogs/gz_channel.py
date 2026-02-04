import discord
from discord.ext import commands
import json
import os

class GzChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gz_channels = self.load_gz_channels()
        self.gz_emoji = "<:gz:1468531948061458463>"
        self.startup_scan_done = False
    
    def load_gz_channels(self):
        """Load gz channels from file"""
        try:
            with open('gz_channels.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_gz_channels(self):
        """Save gz channels to file"""
        with open('gz_channels.json', 'w') as f:
            json.dump(self.gz_channels, f)
    
    @commands.command(name='addgz')
    @commands.is_owner()
    async def add_gz_channel(self, ctx, channel: discord.TextChannel = None):
        """Add a channel to the gz list"""
        if channel is None:
            channel = ctx.channel
        
        if channel.id not in self.gz_channels:
            self.gz_channels.append(channel.id)
            self.save_gz_channels()
            await ctx.send(f"Added {channel.mention} to gz channels! {self.gz_emoji}")
        else:
            await ctx.send(f"{channel.mention} is already a gz channel!")
    
    @commands.command(name='removegz')
    @commands.is_owner()
    async def remove_gz_channel(self, ctx, channel: discord.TextChannel = None):
        """Remove a channel from the gz list"""
        if channel is None:
            channel = ctx.channel
        
        if channel.id in self.gz_channels:
            self.gz_channels.remove(channel.id)
            self.save_gz_channels()
            await ctx.send(f"Removed {channel.mention} from gz channels!")
        else:
            await ctx.send(f"{channel.mention} is not a gz channel!")
    
    async def check_message_for_images(self, message):
        """Check if message has images and react if needed"""
        # Check if message has attachments, embeds with images, or gyazo links
        has_image = False
        
        # Check for gyazo links in message content
        if "gyazo.com/" in message.content:
            has_image = True
        
        if message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    has_image = True
                    break
        
        if message.embeds:
            for embed in message.embeds:
                if embed.image or embed.thumbnail:
                    has_image = True
                    break
        
        if has_image:
            try:
                await message.add_reaction(self.gz_emoji)
            except:
                pass  # Ignore errors (message deleted, no permissions, etc.)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Scan last 5 messages in gz channels on startup"""
        if self.startup_scan_done:
            return
        
        self.startup_scan_done = True
        
        for channel_id in self.gz_channels:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    async for message in channel.history(limit=5):
                        if not message.author.bot:
                            await self.check_message_for_images(message)
            except:
                pass  # Ignore errors

    @commands.Cog.listener()
    async def on_message(self, message):
        """React to images in gz channels"""
        if message.author.bot:
            return
        
        if message.channel.id not in self.gz_channels:
            return
        
        await self.check_message_for_images(message)
    @commands.Cog.listener()
    async def on_message(self, message):
        """React to images in gz channels"""
        if message.author.bot:
            return
        
        if message.channel.id not in self.gz_channels:
            return
        
        await self.check_message_for_images(message)

async def setup(bot):
    await bot.add_cog(GzChannel(bot))