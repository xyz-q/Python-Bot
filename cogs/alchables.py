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
        async with ctx.typing():
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
        
        rows = table.find_all('tr')[1:50]  # Get more items
        item_data = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 7:
                # Extract item name
                item_link = cells[1].find('a')
                item_name = item_link.text if item_link else "Unknown"
                
                # Extract profit
                profit_text = cells[4].text.strip().replace(',', '')
                profit = re.search(r'(\d+)', profit_text)
                profit = int(profit.group(1)) if profit else 0
                
                # Extract volume (daily trades) - column 7
                volume_text = cells[7].text.strip().replace(',', '') if len(cells) > 7 else '0'
                volume = re.search(r'(\d+)', volume_text)
                volume = int(volume.group(1)) if volume else 0
                
                item_data.append((item_name, profit, volume))
        
        # Sort by volume first (descending), then by profit (descending)
        item_data.sort(key=lambda x: x[2], reverse=True)  # Sort by volume only
        
        # Take top 10
        items = []
        for item_name, profit, volume in item_data[:10]:
            items.append(f"**{item_name}** - {profit:,} gp ({volume:,} trades)")
        
        # Send results
        embed = discord.Embed(title="High Alchemy Profits", color=0xFFD700, description="Most profitable items for high alchemy")
        embed.add_field(name="Nature Rune Price", value=f"**{nature_price}** gp", inline=True)
        embed.add_field(name="Top 10 by Volume & Profit", value="\n".join(items) if items else "No items found", inline=False)
        embed.set_footer(text="Data from RuneScape Wiki")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Alchables(bot))