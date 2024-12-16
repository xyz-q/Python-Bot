import discord
from discord.ext import commands
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
            "whip": "abyssal whip",
            "dboot": "dragon boots",
            "scimmy": "amulet of fury",
            "bgloves": "barrows gloves",
            # Add more aliases as needed
        }
        print("PriceChecker cog initialized")

    @commands.Cog.listener()
    async def on_ready(self):
        print("PriceChecker cog is ready")

    def process_item_name(self, item_name: str) -> str:
        """Process item name and check for aliases including compound names"""
        words = item_name.lower().split()
        
        # Check if the last word is an alias
        if words[-1] in self.item_aliases:
            # Replace the last word with its alias
            words[-1] = self.item_aliases[words[-1]]
            return " ".join(words)
            
        # If no alias found, return original name
        return item_name.lower()

    def get_item_id_from_name(self, item_name: str) -> str:
        """Convert item name to item ID using the dictionary"""
        processed_name = self.process_item_name(item_name)
        print(f"Looking up: {processed_name}")  # Debug print
        
        # Exact match first
        for item_id, item_data in self.item_dictionary.items():
            if item_data['value'].lower() == processed_name:
                print(f"Found exact match: {item_id}")  # Debug print
                return str(item_id)
                
        # If no exact match, try partial match
        for item_id, item_data in self.item_dictionary.items():
            if processed_name in item_data['value'].lower():
                print(f"Found partial match: {item_id}")  # Debug print
                return str(item_id)
        
        print("No match found")  # Debug print
        return None

    @commands.command(name='recent', aliases=['price', 'pc'])
    async def check_recent(self, ctx, *, item_name: str = None):
        if item_name is None:
            await ctx.send("Please provide an item name. Usage: ,recent <item name>")
            return

        # Process item name with aliases
        processed_name = self.process_item_name(item_name)
        print(f"Searching for item: {processed_name}")

        # Get item ID using the dictionary
        found_item = None
        
        # Search through the list of dictionaries
        for item in self.item_dictionary:
            if item['value'].lower() == processed_name:
                found_item = item
                break

        if found_item is None:
            await ctx.send(f"Could not find item: {item_name}")
            return

        item_id = found_item['id']

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
                                title=f"Recent Trades for {item_name}",
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

                            # Add footer with date
                            latest_date = trades[0]['date'].split('-')
                            embed.set_footer(text=f"📅{latest_date[2]}/{latest_date[1]}/{latest_date[0]}")

                            await ctx.send(embed=embed)
                        else:
                            await ctx.send(f"Error getting price data: {response.status}")
            
            except Exception as e:
                print(f"Error in check_recent: {e}")
                await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(PriceChecker(bot))
