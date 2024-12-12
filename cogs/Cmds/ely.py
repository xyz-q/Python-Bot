import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

class RecentTrades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary of common item aliases
        self.item_aliases = {
            "fsoa": "Staff of Armadyl",
            "phat": "Partyhat",
            "hween": "Halloween mask",
            "rsh": "Red Santa Hat",
            "bsh": "Black Hanta Hat",
            "push": "Purple Santa Hat",
            "pish": "Pink Santa hat",
            "gsh": "Green Santa hat",



                
        }







        

    @commands.command(name='recent', aliases=['price', 'pc'])
    async def check_recent(self, ctx, *, item_name: str):
        """Check recent trades for a RuneScape 3 item"""
        try:
            item_name = self.item_aliases.get(item_name.lower(), item_name)
            async with ctx.typing():
                formatted_item = item_name.replace(' ', '%20')
                url = f"https://www.ely.gg/search?search_item={formatted_item}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the center-recent div
                center_recent = soup.find('div', class_='center-recent')
                
                if center_recent:
                    # Extract month
                    month = center_recent.find('h4', class_='czMglK')
                    month_text = month.text if month else "Unknown"
                    
                    # Extract day
                    day = center_recent.find('p', class_='iNHHmI')
                    day_text = day.text.strip() if day else "Unknown"
                    
                    # Extract price and transaction type
                    price_div = center_recent.find('h4', class_='bought')
                    if not price_div:
                        price_div = center_recent.find('h4', class_='sold')
                    
                    price_text = price_div.text if price_div else "Unknown"
                    transaction_type = "Bought" if 'bought' in price_div.get('class', []) else "Sold" if price_div else "Unknown"
                    
                    # Extract time
                    time = center_recent.find_all('p', class_='iNHHmI')[1]
                    time_text = time.text.strip() if time else "Unknown"
                    
                    # Extract price change percentage
                    price_change = center_recent.find('p', class_='pricel')
                    price_change_text = price_change.text if price_change else "Unknown"
                    
                    # Create and send embedded message
                    embed = discord.Embed(
                        title=f"Price for - {item_name}",
                        color=discord.Color.gold()
                    )
                    
                    embed.add_field(name="Date", value=f"{month_text} {day_text}", inline=True)
                    embed.add_field(name="Time", value=time_text, inline=True)
                    embed.add_field(name="Transaction", value=f"{transaction_type}: {price_text}", inline=False)
                    embed.add_field(name="Price Change", value=price_change_text, inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("No recent trades found")
                
        except requests.RequestException as e:
            await ctx.send(f"Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"An error occurred while processing the data: {str(e)}")

    @check_recent.error
    async def recent_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide an item name. Usage: `,recent <item name>`")

async def setup(bot):
    await bot.add_cog(RecentTrades(bot))
