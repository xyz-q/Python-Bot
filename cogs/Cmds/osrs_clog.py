import discord
from discord.ext import commands, tasks
import aiohttp
import json
import os
from datetime import datetime

class OSRSCollectionLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = os.path.join('.json', 'osrs-clog-config.json')
        self.config = self.load_config()
        self.username = "R0sa Percs"
        
    def load_config(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"channel_id": None, "found_items": []}
    
    def save_config(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def get_recent_items(self):
        url = f"https://templeosrs.com/api/collection-log/player_recent_items.php?player={self.username}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'error' in data:
                        print(f"Temple API error: {data['error']['Message']}")
                        return []
                    return data.get('data', [])
                return []
    
    @commands.command(name='osrsclog')
    @commands.is_owner()
    async def set_clog_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for OSRS collection log notifications"""
        if channel is None:
            channel = ctx.channel
        
        self.config['channel_id'] = channel.id
        self.save_config()
        await ctx.send(f"OSRS collection log notifications will be sent to {channel.mention}")
    
    @commands.command(name='testosrsclog')
    async def test_clog(self, ctx):
        """Test the TempleOSRS API"""
        await ctx.send("Checking TempleOSRS API...")
        recent_items = await self.get_recent_items()
        
        if not recent_items:
            await ctx.send("No new items found. Make sure you've synced to TempleOSRS and obtained a new item!")
        else:
            await ctx.send(f"Found {len(recent_items)} new items!\n{recent_items}")

async def setup(bot):
    await bot.add_cog(OSRSCollectionLog(bot))
