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
        self.drops_channel_id = 1470263704451809467  # Set the drops channel ID
        self.check_new_drops.start()  # Auto-start the drop checker

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

    async def get_wiki_timestamp(self, item_name):
        """Get timestamp from wiki page"""
        try:
            wiki_name = item_name.strip().replace(' ', '_')
            variations = [
                wiki_name,
                wiki_name.lower(),
                wiki_name.replace('_Robe_Bottoms', '_robe_bottom'),
                wiki_name.replace('_Codex', '_codex'),
                wiki_name.lower().replace('_robe_bottoms', '_robe_bottom'),
            ]
            
            for variant in variations:
                wiki_url = f"https://runescape.wiki/w/{variant}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(wiki_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Look for timestamp inside clock icon element
                            clock_pattern = r'<i class="fa fa-clock-o"[^>]*>([^<]*)</i>'
                            match = re.search(clock_pattern, html)
                            
                            if match:
                                timestamp_text = match.group(1).strip()
                                print(f"Found timestamp: {timestamp_text}")
                                return timestamp_text
                            else:
                                # Debug: look for any clock icon
                                clock_debug = re.search(r'<i[^>]*fa-clock[^>]*>.*?</i>', html)
                                if clock_debug:
                                    print(f"Found clock element: {clock_debug.group(0)}")
                                else:
                                    print(f"No clock element found for {variant}")
                                
                                # Try alternative patterns
                                alt_patterns = [
                                    r'fa-clock-o[^>]*>([^<]+)',
                                    r'(\d{1,2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2})',
                                    r'clock[^>]*>([^<]*\d{1,2}-[A-Za-z]{3}-\d{4}[^<]*)</'
                                ]
                                
                                for alt_pattern in alt_patterns:
                                    alt_match = re.search(alt_pattern, html)
                                    if alt_match:
                                        timestamp_text = alt_match.group(1).strip()
                                        print(f"Found timestamp with alt pattern: {timestamp_text}")
                                        return timestamp_text
            
            return None
            
        except Exception as e:
            print(f"Error getting wiki timestamp: {e}")
            return None
        """Convert date string to time ago format"""
        from datetime import datetime, timedelta
        try:
            # Parse the date format from RuneMetrics API
            trade_date = datetime.strptime(date_str, '%d-%b-%Y %H:%M')
            now = datetime.now()
            delta = now - trade_date
            
            total_minutes = int(delta.total_seconds() / 60)
            
            if total_minutes < 1:
                return "just now"
            elif total_minutes == 1:
                return "1 minute ago"
            elif total_minutes < 60:
                return f"{total_minutes} minutes ago"
            elif total_minutes < 1440:
                hours = total_minutes // 60
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = total_minutes // 1440
                return f"{days} day{'s' if days != 1 else ''} ago"
        except:
            return date_str

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
    
    @commands.command(name='testrs3drops')
    @commands.is_owner()
    async def test_drops(self, ctx):
        """Test the RuneMetrics API"""
        username = "R0SA+PERCS"
        msg = await ctx.send("Checking RuneMetrics API...")
        
        api_url = f"https://apps.runescape.com/runemetrics/profile/profile?user={username}&activities=20"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    activities = data.get('activities', [])
                    drops = [a for a in activities if a.get('text', '').lower().startswith('i found')]
                    
                    await msg.delete()
                    if not drops:
                        await ctx.send("No drops found in recent activities!")
                    else:
                        await ctx.send(f"Found {len(drops)} drops!\n{drops}")
                else:
                    await msg.delete()
                    await ctx.send(f"API error: {response.status}")
    
    @commands.command(name='clearrs3drops')
    @commands.is_owner()
    async def clear_last_drop(self, ctx):
        """Remove the last tracked drop to test notifications"""
        username = "R0SA+PERCS"
        drops = self.load_drops_data(username)
        if drops:
            removed = drops.pop(0)
            self.save_drops_data(username, drops)
            await ctx.send(f"Removed drop: {removed['text']}")
        else:
            await ctx.send("No drops to remove!")
    
    @tasks.loop(seconds=30)
    async def check_new_drops(self):
        """Check for new drops every 30 seconds"""
        username = "R0SA+PERCS"
        channel_id = self.drops_channel_id  # Use the set channel instead of hardcoded
        
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
                                    
                                    # Parse the actual drop date from RuneMetrics
                                    try:
                                        drop_time = datetime.strptime(drop['date'], '%d-%b-%Y %H:%M')
                                        unix_timestamp = int(drop_time.timestamp())
                                        print(f"Parsed drop time: {drop['date']} -> {unix_timestamp}")
                                    except Exception as e:
                                        print(f"Failed to parse timestamp '{drop['date']}': {e}")
                                        # Fallback to current time
                                        unix_timestamp = int(datetime.now().timestamp())
                                    
                                    print(f"Using unix timestamp: {unix_timestamp} for relative time")
                                    
                                    embed = discord.Embed(
                                        title="R0SA PERCS has received a drop!",
                                        description=drop['text'],
                                        color=discord.Color.gold()
                                    )
                                    embed.add_field(name="Time", value=f"<t:{unix_timestamp}:R>", inline=False)
                                    
                                    if image_url:
                                        print(f"Using image URL: {image_url}")
                                        embed.set_thumbnail(url=image_url)
                                    else:
                                        print(f"No image found for: {item_name}")
                                    
                                    message = await channel.send(embed=embed)
                                    await message.add_reaction("<:gz:1468531948061458463>")
                            
                            # Update stored drops
                            all_drops = existing_drops + new_drops
                            self.save_drops_data(username, all_drops[-50:])  # Keep last 50 drops
                        
        except Exception as e:
            print(f"Error checking drops: {e}")
    
async def setup(bot):
    await bot.add_cog(RuneMetrics(bot))