import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

class RuneScape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pc')
    async def price_check(self, ctx, *, item_name):
        try:
            search_terms = item_name.split()
            url = f"https://www.ely.gg/search?search_item={'+'.join(search_terms)}"
            response = requests.get(url)

            if response.status_code != 200:
                await ctx.send(f"An error occurred while fetching the item price. Please try again later.")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            item_containers = soup.select('.item-container')

            if item_containers:
                embed = discord.Embed(title=f"Search Results for '{item_name}'", color=discord.Color.green())
                options = []

                for i, item_container in enumerate(item_containers[:5], start=1):
                    item_price = item_container.select_one('.item-price').text.strip()
                    if any(term.lower() in item_title.lower() for term in search_terms):
                        options.append(f"{i}. {item_title} - {item_price}")

                embed.description = "\n".join(options)
                message = await ctx.send(embed=embed)

                for i in range(1, len(options) + 1):
                    await message.add_reaction(str(i) + "\N{COMBINING ENCLOSING KEYCAP}")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in [str(i) + "\N{COMBINING ENCLOSING KEYCAP}" for i in range(1, len(options) + 1)]

                reaction, _ = await self.bot.wait_for('reaction_add', check=check)
                selected_option = int(reaction.emoji[0])
                selected_item = [item for item in item_containers if any(term.lower() in item.select_one('.item-title').text.strip().lower() for term in search_terms)][selected_option - 1]
                item_name = selected_item.select_one('.item-title').text.strip()
                item_price = selected_item.select_one('.item-price').text.strip()

                embed = discord.Embed(title=item_name, color=discord.Color.green())
                embed.add_field(name='Price', value=item_price)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No items found for '{item_name}'")
        except Exception as e:
            print(f"An error occurred: {e}")
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(RuneScape(bot))
