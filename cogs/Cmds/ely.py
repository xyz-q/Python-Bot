import discord
from discord.ext import commands
from difflib import get_close_matches
import aiohttp
import sys
import os

# Add the parent directory to sys.path to allow imports from there
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from elydata import data

class PriceChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_dictionary = data
        # Add alias dictionary
        self.item_aliases = {
            "fsoa": "Staff of Armadyl",
            "phat": "partyhat",
            "black": "black partyhat",
            "red": "red partyhat",
            "white": "white partyhat",
            "blue": "blue partyhat",
            "green": "green partyhat",
            "purple": "purple partyhat",
            "yellow": "yellow partyhat",
            "bsh": "black santa hat",
            "rsh": "red santa hat",
            "hween": "halloween mask",
            "xmas": "christmas",
            "hsr": "signet ring",
            "osh": "orlando",
            
            
            


            # Add more aliases as needed
        }
        print("PriceChecker cog initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        print("PriceChecker cog is ready")

    from difflib import get_close_matches
    
    def process_item_name(self, item_name: str) -> str:
        """Process item name and check for aliases including compound names"""
        print(f"Processing item name: {item_name}")
        
        # Add compound aliases
        compound_aliases = {
            "black xmas": "black christmas scythe",
            "black xmas scythe": "black christmas scythe",
            # Add other compound aliases here
        }
        
        item_lower = item_name.lower()
        
        # First check complete phrase in compound aliases
        for alias, full_name in compound_aliases.items():
            if alias == item_lower:
                return full_name
        
        # Get all actual item names from dictionary
        all_item_names = [item['value'].lower() for item in self.item_dictionary]
        
        # Try exact match first
        if item_lower in all_item_names:
            return item_lower
            
        # If no exact match, try fuzzy matching the complete phrase
        complete_matches = get_close_matches(item_lower, all_item_names, n=1, cutoff=0.7)
        if complete_matches:
            return complete_matches[0]
            
        # If still no match, try word by word
        words = item_lower.split()
        final_words = []
        
        for word in words:
            # Try exact matches first
            if word in all_item_names:
                final_words.append(word)
                continue
                
            # Then try fuzzy matching
            word_matches = get_close_matches(word, all_item_names, n=1, cutoff=0.7)
            if word_matches:
                final_words.append(word_matches[0])
            else:
                final_words.append(word)
        
        result = " ".join(final_words)
        print(f"Corrected search term: {result}")
        return result
    
    
    
    
    @commands.command(name='recent', aliases=['price', 'pc'])
    async def check_recent(self, ctx, *, item_name: str = None):
        if item_name is None:
            await ctx.send("Please provide an item name. Usage: ,recent <item name>")
            return
    
        original_name = item_name
        processed_name = self.process_item_name(item_name)
        
        if processed_name != item_name.lower():
            print(f"Corrected '{original_name}' to '{processed_name}'")
        
        # Rest of your existing code...
    
    
        # Process item name with aliases
        processed_name = self.process_item_name(item_name)
        print(f"Searching for item: {processed_name}")
    
        matches = []
        exact_matches = []
    
        # Two-pass search: first for exact matches, then for partial
        for item in self.item_dictionary:
            item_name_lower = item['value'].lower()
            if item_name_lower == processed_name:  # Exact match
                exact_matches.append(item)
            elif processed_name in item_name_lower:  # Partial match
                # Only add if it's not already an exact match
                if item not in exact_matches:
                    matches.append(item)
    
        # If we have exact matches, use those instead of partial matches
        if exact_matches:
            matches = exact_matches
    
        if not matches:
            await ctx.send(f"Could not find item: {item_name}")
            return
    
        if len(matches) > 1:
            embed = discord.Embed(
                title="Multiple matches found",
                description="Please be more specific. Found these items:",
                color=discord.Color.blue()
            )
            # Sort matches by length of name to show closest matches first
            matches.sort(key=lambda x: len(x['value']))
            for item in matches[:10]:  # Limit to 10 matches
                embed.add_field(
                    name=item['value'],
                    value=f"ID: {item['id']}",
                    inline=False
                )
            await ctx.send(embed=embed)
            return
    
        found_item = matches[0]
        item_id = found_item['id']
    
        # Rest of your existing price check code...
    
    
        # Show typing indicator while processing
        async with ctx.typing():
            try:
                url = f"https://www.ely.gg/chart/{item_id}/prices"
                print(f"Item Found.")
                print(f"Attempting to fetch URL: {url}")  # Debug print
                
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
                            trades = data['items'][-5:]  # Get last 5 trades
                            trades.reverse()  # Reverse to show newest first
                            
                            embed = discord.Embed(
                                title=f"Recent Trades for {found_item['value']}",
                                color=discord.Color.gold()
                            )
    
                            def format_price(price):
                                return f"{int(price):,}"
    
                            def get_days_ago(date_str):
                                from datetime import datetime
                                trade_date = datetime.strptime(date_str, '%Y-%m-%d-%H:%M')
                                now = datetime.now()
                                delta = now - trade_date
                                if delta.days == 0:
                                    return "today"
                                elif delta.days == 1:
                                    return "1 day ago"
                                else:
                                    return f"{delta.days} days ago"
    
                            def format_percentage(old_price, new_price):
                                percentage = ((new_price - old_price) / old_price) * 100
                                sign = '+' if percentage > 0 else ''
                                return f"({sign}{percentage:.1f}%)"
    
                            # Calculate prices
                            avg_price = sum(trade['price'] for trade in trades) / len(trades)
                            highest_price = max(trade['price'] for trade in trades)
                            lowest_price = min(trade['price'] for trade in trades)
                            margin = highest_price - lowest_price
                            margin_percentage = ((highest_price - lowest_price) / lowest_price) * 100
    
                            # Calculate price trend
                            oldest_price = trades[-1]['price']
                            newest_price = trades[0]['price']
                            trend_percentage = ((newest_price - oldest_price) / oldest_price) * 100
                            trend_symbol = "📈" if trend_percentage > 0 else "📉"
    
                            # Add price information
                            price_info = (
                                f"**Average:** {format_price(avg_price)} gp\n"
                                f"**Margin:** {format_price(margin)} gp ({margin_percentage:.1f}%)\n"
                                f"**Range:** `H: {format_price(highest_price)}` • `L: {format_price(lowest_price)}`\n"
                                f"**Trend:** {trend_symbol} {format_price(oldest_price)} → {format_price(newest_price)} ({'+' if trend_percentage > 0 else ''}{trend_percentage:.1f}%)"
                            )
                            
                            embed.add_field(
                                name="Price Information",
                                value=price_info,
                                inline=False
                            )
    
                            # Create trade history string
                            trade_history = ""
                            for i, trade in enumerate(trades):
                                time = trade['date'].split('-')[-1]
                                days_ago = get_days_ago(trade['date'])
                                price = format_price(trade['price'])
                                
                                if i > 0:
                                    prev_price = trades[i-1]['price']
                                    percentage = format_percentage(prev_price, trade['price'])
                                    trade_history += f"`{time}` ({days_ago}) • {trade['purchase']} for **{price}** gp {percentage}\n"
                                else:
                                    trade_history += f"`{time}` ({days_ago}) • {trade['purchase']} for **{price}** gp\n"
    
                            embed.add_field(
                                name="Recent Trades",
                                value=trade_history,
                                inline=False
                            )
    
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("Error fetching price data.")
            except Exception as e:
                print(f"Error: {e}")
                await ctx.send("An error occurred while fetching price data.")
    
async def setup(bot):
    await bot.add_cog(PriceChecker(bot))
