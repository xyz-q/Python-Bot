import discord
from discord.ext import commands
from difflib import get_close_matches
import aiohttp
import sys
import os
import asyncio


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from elydata import data

class PriceChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_dictionary = data
        

        self.item_aliases = {
            "hween": "halloween mask",


        }
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("PriceChecker cog is ready")

    from difflib import get_close_matches
    
    def process_item_name(self, item_name: str) -> str:
        """Process item name and check for aliases including compound names"""
        print(f"Processing item name: {item_name}")
        

        compound_aliases = {
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

            

            
            


            

            

            

        }
        
        item_lower = item_name.lower()
        
  
        for alias, full_name in compound_aliases.items():
            if alias == item_lower:
                return full_name
        
    
        all_item_names = [item['value'].lower() for item in self.item_dictionary]
        
     
        if item_lower in all_item_names:
            return item_lower
            
     
        complete_matches = get_close_matches(item_lower, all_item_names, n=1, cutoff=0.7)
        if complete_matches:
            return complete_matches[0]
            
 
        words = item_lower.split()
        final_words = []
        
        for word in words:
      
            if word in all_item_names:
                final_words.append(word)
                continue
                
    
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
        
    
    
    

        processed_name = self.process_item_name(item_name)
        print(f"Searching for item: {processed_name}")
    
        matches = []
        exact_matches = []
    
      
        for item in self.item_dictionary:
            item_name_lower = item['value'].lower()
            if item_name_lower == processed_name:  
                exact_matches.append(item)
            elif processed_name in item_name_lower:  

                if item not in exact_matches:
                    matches.append(item)
    

        if exact_matches:
            matches = exact_matches
    
        if not matches:
            await ctx.send(f"Could not find item: {item_name.title()}")
            return
    
        if len(matches) > 1:
            embed = discord.Embed(
                title=f"{item_name.title()}",
                description=f"Prices matching item name - {item_name.title()}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1323062450559516792/phatset.png?ex=6")
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
    
                                      
                            try:
                                base_url = "https://www.ely.gg"
                                icon_path = found_item['icon']
                                
                              
                                if 'cdn.discordapp.com' in icon_path:
                                    icon_url = icon_path.replace('https://www.ely.gghttps://', 'https://')
                                else:
                                    icon_url = base_url + icon_path
                                
                                print(f"Attempting to set thumbnail with URL: {icon_url}")  
                                embed.set_thumbnail(url=icon_url)
                                
                                print(f"Image set found with: {icon_url}")
                                await asyncio.sleep(1)  
                            except Exception as e:
                                print(f"Failed to set thumbnail: {e}")
                            
                            

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
                            trend_symbol = "<:up:1320181605918183496>" if trend_percentage > 0 else "<:down:1320181619406929970>"
    
                            price_info = (
                                
                                f"**Current Street Price** <:goldpoints:1319902464115343473> ***{format_price(newest_price)}***\n\n"
                                f"**Margin:**<:margin:1320185569703100470>({margin_percentage:.1f}%) ~ ***{format_price(margin)}***\n\n"                              
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
