import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, time
import json



class MerchantUpdater(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_merchant_stock.start()

    def cog_unload(self):
        self.update_merchant_stock.cancel()

    @tasks.loop(time=time(hour=23, minute=59, second=55))
    async def update_merchant_stock(self):
        """Update merchant stock data daily at UTC midnight"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            stock = {}  # Initialize empty stock dictionary
            async with session.get('https://runescape.wiki/w/Travelling_Merchant%27s_Shop/Future', headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    table = soup.find('table', class_="wikitable sticky-header")
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header row
                        
                        for row in rows[:30]:  # Limit to 30 days
                            date_cell = row.find('td')
                            if date_cell:
                                date = date_cell.text.strip()
                                
                                items = []
                                inventory_cells = row.find_all('td', class_="inventory-image")
                                for cell in inventory_cells:
                                    anchor = cell.find('a')
                                    if anchor and anchor.get('title'):
                                        items.append(anchor['title'])
                                
                                if items:
                                    stock[date] = items

                    
                    
                    # Save to JSON file
                    with open('merchant_stock.py', 'w') as f:
                        f.write(f"stock = {repr(stock)}\n")
                    
                    print(f"Updated merchant stock data at {datetime.utcnow().isoformat()}")

    @update_merchant_stock.before_loop
    async def before_update(self):
        """Wait for bot to be ready before starting the task"""
        await self.bot.wait_until_ready()
        # Run once when loaded
        await self.update_merchant_stock()

    @commands.command(name="stockupdate", aliases=['merchupdate'])
    @commands.is_owner()
    async def update_merchant_command(self, ctx):
        """Manually update the merchant stock data"""
        await ctx.send("Updating merchant stock data...")
        await self.update_merchant_stock()
        await ctx.send("Merchant stock data has been updated!")

    @update_merchant_command.error
    async def update_merchant_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")



    
async def setup(bot):
    await bot.add_cog(MerchantUpdater(bot))
