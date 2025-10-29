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
        html = await self.fetch_alch_data()
        if not html:
            await ctx.send("Failed to fetch data from wiki")
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find nature rune price
        nature_span = soup.find('span', class_='nocoins coins-pos')
        nature_price = nature_span.text.strip() if nature_span else "Not found"
        
        # Find the table with alchemy data
        table = soup.find('table', class_='wikitable')
        if not table:
            await ctx.send("Could not find alchemy table")
            return
        
        # Filter for practical alchables only
        excluded_keywords = ['uncut', 'primal', 'corrupt', 'ancient', 'salvage', 'royal', 'dormant', 'huge', 'large', 'medium', 'small', 'tiny']
        
        # Include common alchables
        include_keywords = ['bolts', 'battlestaff', 'bracelet', 'dust', 'amulet', 'necklace', 'ring']
        
        rows = table.find_all('tr')[1:50]  # Get more items to filter from
        items = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                # Extract item name
                item_link = cells[1].find('a')
                item_name = item_link.text if item_link else "Unknown"
                
                # Extract profit and price
                profit_text = cells[4].text.strip().replace(',', '')
                profit = re.search(r'(\d+)', profit_text)
                profit = int(profit.group(1)) if profit else 0
                
                price_text = cells[2].text.strip().replace(',', '')
                price = re.search(r'(\d+)', price_text)
                price = int(price.group(1)) if price else 0
                
                # Filter for practical items
                is_excluded = any(keyword in item_name.lower() for keyword in excluded_keywords)
                is_included = any(keyword in item_name.lower() for keyword in include_keywords)
                
                if (profit > 100 and  # Higher minimum profit
                    price < 50000 and  # Lower max price
                    not is_excluded and
                    (is_included or 'staff' in item_name.lower())):
                    items.append(f"**{item_name}** - {profit:,} gp")
                    
                if len(items) >= 10:  # Stop at 10 items
                    break
        
        # Send results
        embed = discord.Embed(title="High Alchemy Profits", color=0xFFD700, description="Most profitable items for high alchemy")
        embed.add_field(name="Nature Rune Price", value=f"**{nature_price}** gp", inline=True)
        embed.add_field(name="Top 10 Practical Items", value="\n".join(items) if items else "No items found", inline=False)
        embed.set_footer(text="Data from RuneScape Wiki")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Alchables(bot))