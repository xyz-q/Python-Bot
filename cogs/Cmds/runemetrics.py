import discord
from discord.ext import commands, tasks
import aiohttp
import json
import re
import os
from datetime import datetime

class RuneMetrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_wiki_image_url(self, item_name):
        """Search for RuneScape Wiki image URL by parsing HTML"""
        try:
            wiki_name = item_name.strip().replace(' ', '_')
            # Try different variations
            variations = [
                wiki_name,  # Original
                wiki_name.lower(),  # All lowercase
                wiki_name.replace('_Robe_Bottoms', '_robe_bottom'),  # Fix plurals
                wiki_name.replace('_Codex', '_codex'),  # Fix case
                wiki_name.lower().replace('_robe_bottoms', '_robe_bottom'),  # Lowercase + fix plurals
            ]
            
            for variant in variations:
                wiki_url = f"https://runescape.wiki/w/{variant}"
                print(f"Trying wiki URL: {wiki_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(wiki_url) as response:
                        print(f"Response status: {response.status} for {variant}")
                        if response.status == 200:
                            html = await response.text()
                            pattern = r'<figure[^>]*mw-halign-left[^>]*>.*?<img src="(/images/thumb/[^"]+\.png/\d+px-[^"]+\.png[^"]*)'
                            match = re.search(pattern, html, re.DOTALL)
                            
                            if match:
                                return f"https://runescape.wiki{match.group(1)}"
                            else:
                                # Debug: print a snippet of HTML to see the structure
                                img_snippet = re.search(r'<img[^>]*src="[^"]*detail\.png[^"]*"[^>]*>', html)
                                if img_snippet:
                                    print(f"Found img tag: {img_snippet.group(0)}")
                                else:
                                    print(f"No img tag with detail.png found for {variant}")
                                print(f"No image pattern match for {variant}")
            
            print(f"Wiki page not found for {item_name}")
            return None
            
        except Exception as e:
            print(f"Error searching for item image: {e}")
            return None

    @commands.command(name='testimg')
    async def test_images(self, ctx):
        """Test the 3 specific images"""
        test_items = ['Shard of Genesis Essence', 'Praesul Codex', 'Vestments of Havoc Robe Bottoms']
        
        for item in test_items:
            image_url = await self.get_wiki_image_url(item)
            if image_url:
                await ctx.send(f"{item}: {image_url}")
            else:
                await ctx.send(f"{item}: No image found")

    def load_drops_data(self, username):
        """Load existing drops data from JSON"""
        filename = f"{username.lower().replace('+', '-')}-drops.json"
        filepath = os.path.join('.json', filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return []
    
    def save_drops_data(self, username, drops):
        """Save drops data to JSON"""
        filename = f"{username.lower().replace('+', '-')}-drops.json"
        filepath = os.path.join('.json', filename)
        
        with open(filepath, 'w') as f:
            json.dump(drops, f, indent=2)
    
    @tasks.loop(minutes=5)
    async def check_new_drops(self):
        """Check for new drops every 5 minutes"""
        username = "R0SA+PERCS"
        channel_id = 123456789  # Replace with your channel ID
        
        try:
            # Get current drops
            api_url = f"https://apps.runescape.com/runemetrics/profile/profile?user={username}&activities=20"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        activities = data.get('activities', [])
                        
                        current_drops = []
                        for activity in activities:
                            text = activity.get('text', '')
                            if text.lower().startswith('i found'):
                                current_drops.append({
                                    'text': text,
                                    'date': activity.get('date'),
                                    'timestamp': datetime.now().isoformat()
                                })
                        
                        # Load existing drops
                        existing_drops = self.load_drops_data(username)
                        existing_texts = [drop['text'] for drop in existing_drops]
                        
                        # Find new drops
                        new_drops = [drop for drop in current_drops if drop['text'] not in existing_texts]
                        
                        if new_drops:
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                for drop in new_drops:
                                    item_match = re.search(r'I found (?:a |an |some )?(.*)', drop['text'], re.IGNORECASE)
                                    item_name = item_match.group(1) if item_match else drop['text']
                                    
                                    image_url = await self.get_wiki_image_url(item_name)
                                    
                                    embed = discord.Embed(
                                        title="New Drop!",
                                        description=drop['text'],
                                        color=discord.Color.green(),
                                        timestamp=datetime.fromisoformat(drop['timestamp'])
                                    )
                                    
                                    if image_url:
                                        embed.set_thumbnail(url=image_url)
                                    
                                    await channel.send(embed=embed)
                            
                            # Update stored drops
                            all_drops = existing_drops + new_drops
                            self.save_drops_data(username, all_drops[-50:])  # Keep last 50 drops
                        
        except Exception as e:
            print(f"Error checking drops: {e}")
    
    @commands.command(name='startdrops')
    async def start_drop_checker(self, ctx):
        """Start the automatic drop checker"""
        if not self.check_new_drops.is_running():
            self.check_new_drops.start()
            await ctx.send("Drop checker started!")
        else:
            await ctx.send("Drop checker is already running!")
    
    @commands.command(name='stopdrops')
    async def stop_drop_checker(self, ctx):
        """Stop the automatic drop checker"""
        if self.check_new_drops.is_running():
            self.check_new_drops.cancel()
            await ctx.send("Drop checker stopped!")
        else:
            await ctx.send("Drop checker is not running!")
    async def check_drops(self, ctx, username: str = "R0SA+PERCS"):
        api_url = f"https://apps.runescape.com/runemetrics/profile/profile?user={username}&activities=20"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        activities = data.get('activities', [])
                        found_items = []
                        
                        for activity in activities:
                            text = activity.get('text', '')
                            if text.lower().startswith('i found'):
                                # Extract item name from "I found a/an/some [item]"
                                item_match = re.search(r'I found (?:a |an |some )?(.*)', text, re.IGNORECASE)
                                item_name = item_match.group(1) if item_match else text
                                
                                found_items.append({
                                    'text': text,
                                    'item_name': item_name,
                                    'date': activity.get('date')
                                })
                        
                        if found_items:
                            # Replace + with space in username for display
                            display_username = username.replace('+', ' ')
                            embed = discord.Embed(
                                title=f"Recent Drops - {display_username}",
                                color=discord.Color.gold()
                            )
                            
                            for item in found_items[:10]:
                                wiki_image = await self.get_wiki_image_url(item['item_name'])
                                embed.add_field(
                                    name="Drop",
                                    value=f"[{item['text']}]({wiki_image}) ({item['date']})",
                                    inline=False
                                )
                            
                            # Set thumbnail to first item's image
                            if found_items:
                                first_item_image = await self.get_wiki_image_url(found_items[0]['item_name'])
                                embed.set_thumbnail(url=first_item_image)
                            
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send(f"No recent drops found for {username}")
                    else:
                        await ctx.send(f"Error fetching data: Status {response.status}")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

async def setup(bot):
    await bot.add_cog(RuneMetrics(bot))