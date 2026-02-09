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
    
    async def get_full_log(self):
        url = f"https://templeosrs.com/api/collection-log/player_collection_log.php?player={self.username}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
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
    
    @commands.command(name='osrsclogview')
    async def view_log(self, ctx):
        """View your full collection log stats"""
        await ctx.send("Fetching collection log...")
        log_data = await self.get_full_log()
        
        if not log_data:
            await ctx.send("Failed to fetch collection log!")
            return
        
        if 'error' in log_data:
            await ctx.send(f"Error: {log_data['error']['Message']}")
            return
        
        data = log_data.get('data', {})
        
        embed = discord.Embed(
            title=f"{data.get('player_name_with_capitalization', self.username)}'s Collection Log",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Collections", value=f"{data.get('total_collections_finished', 0):,} / {data.get('total_collections_available', 0):,}", inline=True)
        embed.add_field(name="Categories", value=f"{data.get('total_categories_finished', 0):,} / {data.get('total_categories_available', 0):,}", inline=True)
        embed.add_field(name="EHC", value=f"{data.get('ehc', 0):.2f}", inline=True)
        embed.set_footer(text=f"Last updated: {data.get('last_changed', 'Unknown')}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OSRSCollectionLog(bot))
