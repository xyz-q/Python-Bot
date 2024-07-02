from discord.ext import commands
import requests

API_KEY = 'iyS7i5NaWNio8kRzLs1EJVTxhCG-YeEN'  # Replace with your actual API key

class Price(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def price(self, ctx, def_index: int, paint_index: int, max_float: float = 0.07):
        search_url = f'https://csfloat.com/search?max_float={max_float}&def_index={def_index}&paint_index={paint_index}&key={API_KEY}'
        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and data['items']:
                lowest_price = min(item['price'] for item in data['items'])
                await ctx.send(f'The current lowest price for def_index {def_index} and paint_index {paint_index} with max float {max_float} is {lowest_price}.')
            else:
                await ctx.send(f'No items found for def_index {def_index} and paint_index {paint_index} with max float {max_float}.')
        else:
            await ctx.send(f'Error fetching data: {response.status_code}')

async def setup(bot):
    await bot.add_cog(Price(bot))
