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
        self.check_new_items.start()
        
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
    
    async def get_item_image(self, item_name):
        url = f"https://oldschool.runescape.wiki/api.php?action=query&titles={item_name}&prop=pageimages&format=json&pithumbsize=250"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get('query', {}).get('pages', {})
                    for page in pages.values():
                        return page.get('thumbnail', {}).get('source')
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
    @commands.is_owner()
    async def test_clog(self, ctx):
        """Test the TempleOSRS API"""
        msg = await ctx.send("Checking TempleOSRS API...")
        recent_items = await self.get_recent_items()
        
        await msg.delete()
        if not recent_items:
            await ctx.send("No new items found. Make sure you've synced to TempleOSRS and obtained a new item!")
        else:
            await ctx.send(f"Found {len(recent_items)} new items!\n{recent_items}")
    
    @commands.command(name='osrsclogview')
    @commands.is_owner()
    async def view_log(self, ctx):
        """View your full collection log stats"""
        msg = await ctx.send("Fetching collection log...")
        log_data = await self.get_full_log()
        
        if not log_data:
            await msg.edit(content="Failed to fetch collection log!")
            return
        
        if 'error' in log_data:
            await msg.edit(content=f"Error: {log_data['error']['Message']}")
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
        
        await msg.delete()
        await ctx.send(embed=embed)
    
    @commands.command(name='osrsclogclear')
    @commands.is_owner()
    async def clear_last(self, ctx):
        """Remove the last tracked item to test notifications"""
        if self.config['found_items']:
            removed = self.config['found_items'].pop()
            self.save_config()
            await ctx.send(f"Removed item ID: {removed}")
        else:
            await ctx.send("No items to remove!")
    
    @tasks.loop(seconds=30)
    async def check_new_items(self):
        if not self.config.get('channel_id'):
            return
        
        channel = self.bot.get_channel(self.config['channel_id'])
        if not channel:
            return
        
        recent_items = await self.get_recent_items()
        for item in recent_items:
            item_id = item.get('id')
            if item_id not in self.config['found_items']:
                self.config['found_items'].append(item_id)
                
                item_name = item.get('name')
                
                # Get full log data for item count
                log_data = await self.get_full_log()
                total_obtained = 0
                total_items = 0
                if log_data and 'data' in log_data:
                    total_obtained = log_data['data'].get('total_obtained', 0)
                    total_items = log_data['data'].get('total_items', 0)
                
                embed = discord.Embed(
                    title="New Collection Log Item!",
                    description=f"\n**R0SA PERCS** found a **{item_name}**",
                    color=discord.Color.gold(),
                    timestamp=datetime.fromisoformat(item.get('date'))
                )
                
                if total_items > 0:
                    embed.add_field(name="Collection Log", value=f"{total_obtained:,} / {total_items:,}", inline=False)
                
                image_url = await self.get_item_image(item_name)
                if image_url:
                    embed.set_thumbnail(url=image_url)
                
                message = await channel.send(embed=embed)
                await message.add_reaction("<:gz:1468531948061458463>")
        
        if recent_items:
            self.save_config()
    
    @check_new_items.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(OSRSCollectionLog(bot))
