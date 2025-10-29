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

    @commands.command(name='alchables')
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
        
        rows = table.find_all('tr')[1:]  # Get ALL items
        item_data = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 9:
                # Extract item name (column 1)
                item_link = cells[1].find('a')
                item_name = item_link.text if item_link else "Unknown"
                
                # Extract profit (column 4)
                profit_text = cells[4].text.strip().replace(',', '')
                profit = re.search(r'(\d+)', profit_text)
                profit = int(profit.group(1)) if profit else 0
                
                # Extract ROI (column 5)
                roi_text = cells[5].text.strip()
                
                # Extract limit (column 6)
                limit_text = cells[6].text.strip().replace(',', '')
                limit = re.search(r'(\d+)', limit_text)
                limit = int(limit.group(1)) if limit else 0
                
                # Extract trade volume (column 7)
                volume_text = cells[7].text.strip().replace(',', '')
                volume = re.search(r'(\d+)', volume_text)
                volume = int(volume.group(1)) if volume else 0
                
                # Extract max profit (column 8)
                max_profit_text = cells[8].text.strip().replace(',', '')
                max_profit = re.search(r'(\d+)', max_profit_text)
                max_profit = int(max_profit.group(1)) if max_profit else 0
                
                item_data.append((item_name, profit, volume, roi_text, limit, max_profit))
        
        # Sort by volume (descending)
        item_data.sort(key=lambda x: x[2], reverse=True)
        
        # Take top 10 by volume
        items = []
        for item_name, profit, volume, roi, limit, max_profit in item_data[:10]:
            items.append(f"**{item_name}** - {profit:,} gp | {roi} ROI | Limit: {limit:,} | Max: {max_profit:,} gp")
        
        # Send results
        embed = discord.Embed(title="High Alchemy Profits", color=0xFFD700, description="*Written by* <@110927272210354176>")
        embed.add_field(name="Nature Rune Price", value=f"**{nature_price}** gp", inline=True)
        embed.add_field(name="Top 10 by Volume", value="\n".join(items) if items else "No items found", inline=False)
        embed.set_footer(text="Data from RuneScape Wiki")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Alchables(bot))