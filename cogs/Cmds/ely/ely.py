import discord
from discord.ext import commands
from difflib import get_close_matches
import aiohttp
import json
import os
import asyncio

def load_ely_data():
    with open(os.path.join(os.path.dirname(__file__), 'elydata.json'), 'r') as f:
        return json.load(f)

class PriceChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_dictionary = load_ely_data()
        self.api_disabled = True  # Set to False when API is back online
        
        self.item_aliases = {
            "hween": "halloween mask",
        }
        
    async def search_item_image(self, item_name: str) -> str:
        """Search for RuneScape Wiki image URL based on item name"""
        try:
            # Convert item name to wiki format (replace spaces with underscores, capitalize)
            wiki_name = item_name.replace(' ', '_').title().replace("'S", "'s")
            
            # Try common wiki image patterns
            wiki_patterns = [
                f"{wiki_name}_detail.png",
                f"{wiki_name}.png",
                f"{wiki_name}_icon.png"
            ]
            
            for pattern in wiki_patterns:
                wiki_url = f"https://runescape.wiki/images/thumb/{pattern}/100px-{pattern}"
                
                # Test if image exists
                async with aiohttp.ClientSession() as session:
                    async with session.head(wiki_url) as response:
                        if response.status == 200:
                            return wiki_url
            
            # Fallback
            return "https://cdn.discordapp.com/attachments/1241642636796887171/1323062450559516792/phatset.png"
            
        except Exception as e:
            print(f"Error searching for item image: {e}")
            return "https://cdn.discordapp.com/attachments/1241642636796887171/1323062450559516792/phatset.png"
        


    from difflib import get_close_matches
    
    def process_item_name(self, item_name: str) -> str:
        """Process item name and check for aliases including compound names"""
        print(f"Processing item name: {item_name}")
        
        # Normalize apostrophes and special characters
        def normalize_name(name):
            return name.lower().replace("'", "").replace("'", "").replace("`", "")
        
        # Create acronyms automatically
        acronym_map = {}
        for item in self.item_dictionary:
            name = item['value'].lower()
            words = name.split()
            if len(words) > 1:
                acronym = ''.join(word[0] for word in words)
                if acronym not in acronym_map:
                    acronym_map[acronym] = name

        compound_aliases = {
            "tumekens": "tumeken's",
            "black xmas": "black christmas scythe",
            "black xmas scythe": "black christmas scythe",         
            "2a": "second age",
            "3a": "third age",
             "3a dye": "third age dye",
            "3a top": "third age platebody",
            "3a bottoms": "third age platelegs",
            "walks": "walk",
            "scythes": "scythe",
            "disk": "disk of returning",
            "xmas": "christmas",
            "bph": "black partyhat",
            "black": "black partyhat",
            "red": "red partyhat",
            "white": "white partyhat",
            "blue": "blue partyhat",
            "green": "green partyhat",
            "purple": "purple partyhat",
            "yellow": "yellow partyhat",
            "bsh": "black santa hat",
            "rsh": "red santa hat",
            "gsh": "green santa hat",
            "ash": "aurora santa hat",
            "rainbow trail": "rainbow trail aura override token",
            "aurora trail": "aurora trail aura override token",
            "aurora scarf": "winter scarf",
            "aurora": "auro",
            "hween": "halloween mask",
            "h'ween": "halloween mask",
            "xmas": "christmas",
            "hsr": "signet ring",
            "osh": "orlando",            
            "bcs": "black christmas scythe",            
            "phats": "partyhat",
            "phat set": "partyhat",
            "phat set": "partyhat",
            "phat": "partyhat",
            "hween set": "halloween mask",
            "hweens": "halloween mask",
            "santas": "santa hat",
            "blue hween": "blue halloween mask",
            "green hween": "green halloween mask",
            "red hween": "red halloween mask",
            "purple hween": "purple halloween mask",
            "orange hween": "orange halloween mask",
            "orange": "orange halloween mask",
            "taggas": "tagga's",
            "fyre": "sana's fyrtorch",
            "hypno": "skeka's hypnowand",
            "titles": "demonic",
            "title": "demonic",
            "gnome": "gnome scarf",
            "gote": "grace of the elves",
            "chalo": "challenger halo",
            "osh": "orlando smith",
            "fsoa": "staff of armadyl", 
            "ecb": "eldritch crossbow",
            "bolg": "bow of the last guardian",
            "ezk": "ek-zekkil",
            "sgb": "seren godbow",
            "eof" : "essence of finality",
            "soul": "soul dye",
            "nox": "noxious",
            "ash": "aurora santa hat", 
            "dyes": "dye",
            "leng": "dark shard of leng",
            "sliver": "dark sliver of leng",
            "manuscripts": "manus",
            "scripts": "scriptu",
            "scriptures": "scriptu",
            "pink": "pink santa hat"
        }
        
        # Merge acronyms with manual aliases
        compound_aliases.update(acronym_map)
        
        item_lower = item_name.lower()
        item_normalized = normalize_name(item_name)
        
        # Auto-handle "set" searches - remove "set" and search for the base name
        if item_lower.endswith(' set'):
            base_name = item_lower[:-4]  # Remove " set"
            return base_name
        
        # Check aliases first (including normalized versions)
        print(f"DEBUG: Checking aliases for '{item_lower}' (normalized: '{item_normalized}')")
        for alias, full_name in compound_aliases.items():
            if alias == item_lower or normalize_name(alias) == item_normalized:
                print(f"DEBUG: Found alias match: {alias} -> {full_name}")
                return full_name
        
        all_item_names = [item['value'].lower() for item in self.item_dictionary]
        all_item_names_normalized = [normalize_name(item['value']) for item in self.item_dictionary]
        
        # Try exact match first
        if item_lower in all_item_names:
            return item_lower
            
        # Try normalized match (without apostrophes)
        if item_normalized in all_item_names_normalized:
            idx = all_item_names_normalized.index(item_normalized)
            return all_item_names[idx]
            
        # If no matches found, return original search term
        print(f"Corrected search term: {item_lower}")
        return item_lower
    
    
    
    
    @commands.command(name='recent', aliases=['price', 'pc'])
    async def check_recent(self, ctx, *, item_name: str = None):
        if self.api_disabled:
            embed = discord.Embed(
                title="🚫 Price Bot Temporarily Out of Service",
                description="The Ely.gg API is currently down. Price checking is temporarily unavailable.\n\nWe'll restore service as soon as the API is back online.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Thank you for your patience!")
            await ctx.send(embed=embed)
            return
            
        if item_name is None:
            await ctx.send("Please provide an item name. Usage: ,recent <item name>")
            return
    
        original_name = item_name
        processed_name = self.process_item_name(item_name)
        
        if processed_name != item_name.lower():
            print(f"Corrected '{original_name}' to '{processed_name}'")
        
    
    
    

        processed_name = self.process_item_name(item_name)
        print(f"Searching for item: {processed_name}")
    
        matches = []
        exact_matches = []
        
        # Normalize function for consistent matching
        def normalize_name(name):
            return name.lower().replace("'", "").replace("'", "").replace("`", "")
        
        processed_normalized = normalize_name(processed_name)
        print(f"DEBUG: Searching for '{processed_name}' (normalized: '{processed_normalized}')")
    
        for item in self.item_dictionary:
            item_name_lower = item['value'].lower()
            item_name_normalized = normalize_name(item['value'])
            
            # Exact matches get highest priority
            if item_name_lower == processed_name or item_name_normalized == processed_normalized:  
                print(f"DEBUG: Exact match found: {item['value']}")
                exact_matches.append(item)
            # For partial matches, only match if the search term starts with the item name or vice versa
            elif (item_name_lower.startswith(processed_name) or processed_name.startswith(item_name_lower) or
                  item_name_normalized.startswith(processed_normalized) or processed_normalized.startswith(item_name_normalized)):
                if item not in exact_matches:
                    print(f"DEBUG: Partial match found: {item['value']}")
                    matches.append(item)
    
        print(f"DEBUG: Found {len(exact_matches)} exact matches, {len(matches)} partial matches")

        if exact_matches:
            matches = exact_matches
    
        # If no matches found, try fuzzy matching as last resort
        if not matches:
            print(f"DEBUG: No matches found, trying fuzzy matching...")
            all_item_names_normalized = [normalize_name(item['value']) for item in self.item_dictionary]
            fuzzy_matches = get_close_matches(processed_normalized, all_item_names_normalized, n=3, cutoff=0.85)
            print(f"DEBUG: Fuzzy matches found: {fuzzy_matches}")
            for fuzzy_match in fuzzy_matches:
                idx = all_item_names_normalized.index(fuzzy_match)
                print(f"DEBUG: Adding fuzzy match: {self.item_dictionary[idx]['value']}")
                matches.append(self.item_dictionary[idx])
    
        if not matches:
            await ctx.send(f"Could not find item: {item_name.title()}")
            return
    
        if len(matches) > 1:
            embed = discord.Embed(
                title=f"{item_name.title()}",
                description=f"Prices matching item name - {item_name.title()}",
                color=discord.Color.gold()
            )
            # Search for appropriate image for multiple matches
            image_url = await self.search_item_image(processed_name)
            embed.set_thumbnail(url=image_url)
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Opera GX";v="114"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0 (Edition std-1)'
            }
        
            async def fetch_single_item(session, item):
                url = f"https://www.ely.gg/chart/{item['id']}/prices"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            recent_trades = data['items'][-8:]
                            
                            if recent_trades:
                                prices = [trade['price'] for trade in recent_trades]
                                min_price = min(prices)
                                max_price = max(prices)
                                return item['value'], f"Range: {min_price:,} - {max_price:,} <:goldpoints:1319902464115343473> "
                            return item['value'], "No recent trades"
                        return item['value'], f"Error: Status {response.status}"
                except Exception as e:
                    print(f"Error fetching prices for {item['value']}: {e}")
                    return item['value'], f"Error fetching prices: {str(e)}"
        
            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                  
                    tasks = [fetch_single_item(session, item) for item in matches[:10]]
                 
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                  
                    for result in results:
                        if isinstance(result, Exception):
                            print(f"Error in fetch: {result}")
                            continue
                        item_name, price_range = result
                        embed.add_field(
                            name=item_name,
                            value=price_range,
                            
                            inline=False
                        )
        
            await ctx.send(embed=embed)
            return
        
        
        
    
        found_item = matches[0]
        item_id = found_item['id']
    

    
    
    
        async with ctx.typing():
            try:
                url = f"https://www.ely.gg/chart/{item_id}/prices"
                print(f"Item Found.")
                print(f"Attempting to fetch URL: {url}") 
                
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'priority': 'u=1, i',
                    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Opera GX";v="114"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0 (Edition std-1)'
                }
    
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            trades = data['items'][-8:]  
                            trades.reverse()  
                            
                            embed = discord.Embed(
                                
                                description="*Written by* <@110927272210354176>",
                                title=f"{found_item['value']}",
                                color=discord.Color.gold()
                            )
    
                                      
                            # Search for and set item image
                            image_url = await self.search_item_image(found_item['value'])
                            embed.set_thumbnail(url=image_url)
                            print(f"Image set found with: {image_url}")
                            
                            

                            def format_price(price):
                                return f"{int(price):,}"


    
                            def get_time_ago(date_str):
                                from datetime import datetime, timedelta
                                trade_date = datetime.strptime(date_str, '%Y-%m-%d-%H:%M')
                                
                               
                                trade_date = trade_date - timedelta(hours=8)
                                
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
                                    minutes = total_minutes % 60
                                    if minutes == 0:
                                        return f"{hours} hours ago"
                                    return f"{hours}h {minutes}m ago"
                                else:
                                    days = total_minutes // 1440
                                    return f"{days} days ago"
                            
                            
    
                            def format_percentage(old_price, new_price):
                                percentage = ((new_price - old_price) / old_price) * 100
                                sign = '+' if percentage > 0 else ''
                                return f"({sign}{percentage:.1f}%)"
    
                         
                            avg_price = sum(trade['price'] for trade in trades) / len(trades)
                            highest_price = max(trade['price'] for trade in trades)
                            lowest_price = min(trade['price'] for trade in trades)
                            margin = highest_price - lowest_price
                            margin_percentage = ((highest_price - lowest_price) / lowest_price) * 100
    
                          
                            oldest_price = trades[-1]['price']
                            newest_price = trades[0]['price']
                            trend_percentage = ((newest_price - oldest_price) / oldest_price) * 100
                            trend_symbol = " <:upward:1328517849861324931> " if trend_percentage > 0 else " <:downward:1328517880882532372> "
                            last_three_trades = trades[-3:]  # Get last 3 trades
                            highest_recent = max(trade['price'] for trade in last_three_trades)
                            lowest_recent = min(trade['price'] for trade in last_three_trades)

                            price_info = (
                                f"**Current Street Price** <:goldpoints:1319902464115343473> ***{format_price(lowest_recent)} - {format_price(highest_recent)}***\n\n"
                                f"**Margin:** <:margin:1320185569703100470> ({margin_percentage:.1f}%) ~ ***{format_price(margin)}***\n\n"                              
                                f"**Trend:** {trend_symbol} ({'+' if trend_percentage > 0 else ''}{trend_percentage:.1f}%) ~ **{format_price(oldest_price)}** → ***{format_price(newest_price)}*** \n\n"
                                f" \u200B \n"
                            )
                                                        
                            embed.add_field(
                                name=f"",
                                value=price_info,
                                inline=False
                            )
                            
                       
                            trade_history = ""
                            for i, trade in enumerate(trades):
                                time = trade['date'].split('-')[-1]
                                time_ago = get_time_ago(trade['date']) 
                                price = format_price(trade['price'])
                                
                                if i > 0:
                                    prev_price = trades[i-1]['price']
                                    percentage = format_percentage(prev_price, trade['price'])
                                    trade_history += f" **({time_ago})** • *{trade['purchase']}* for ***{price}***  {percentage}\n"
                                else:
                                    trade_history += f" **({time_ago})** • *{trade['purchase']}* for ***{price}*** \n"
                            
                            embed.add_field(
                                name="**Recent Trades**",
                                value=trade_history,
                                inline=False
                            )
                            embed.set_footer(text="Use ,alert to get notified when the price changes! ")
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("Error fetching price data.")
            except Exception as e:
                print(f"Error: {e}")
                await ctx.send("An error occurred while fetching price data.")
    
async def setup(bot):
    await bot.add_cog(PriceChecker(bot))
