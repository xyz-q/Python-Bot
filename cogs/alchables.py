import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import re

class Alchables(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wiki_url = "https://runescape.wiki/w/RuneScape:Grand_Exchange_Market_Watch/Alchemy"

    async def fetch_alch_data(self):
        """Fetch alchemy data from RuneScape wiki"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.wiki_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return html
                else:
                    return None

    @commands.command(name='alchtest')
    async def test_alch_data(self, ctx):
        """Test command to see what data we get"""
        await ctx.send("Fetching alchemy data...")
        
        html = await self.fetch_alch_data()
        if not html:
            await ctx.send("Failed to fetch data from wiki")
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find nature rune price
        nature_rune_text = soup.find(text=re.compile(r"nature rune, currently"))
        nature_price = "Not found"
        if nature_rune_text:
            price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*coins', nature_rune_text)
            if price_match:
                nature_price = price_match.group(1)
        
        # Find the table with alchemy data
        table = soup.find('table', class_='wikitable')
        if not table:
            await ctx.send("Could not find alchemy table")
            return
        
        rows = table.find_all('tr')[1:6]  # Get first 5 items (skip header)
        items = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                # Extract item name
                item_link = cells[1].find('a')
                item_name = item_link.text if item_link else "Unknown"
                
                # Extract profit
                profit_text = cells[4].text.strip().replace(',', '')
                profit = re.search(r'(\d+)', profit_text)
                profit = profit.group(1) if profit else "0"
                
                items.append(f"{item_name}: {profit} gp profit")
        
        # Send results
        embed = discord.Embed(title="Alchemy Data Test", color=0x00ff00)
        embed.add_field(name="Nature Rune Price", value=f"{nature_price} gp", inline=False)
        embed.add_field(name="Top 5 Items", value="\n".join(items) if items else "No items found", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Alchables(bot))