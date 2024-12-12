import discord
from discord.ext import commands
import requests

class CSFloatSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = 'https://csfloat.com/api/v1/listings'

    @commands.command(name='csfloat', aliases=['csfloat'])
    async def csfloat_search(self, ctx, *, query):
        try:
            # Prepare the query parameters
            params = {
                'market_hash_name': query,
                'sort_by': 'lowest_price',
                'limit': 50  # Adjust limit as needed
            }

            # Make the request to CSFloat API
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()

            # Parse the JSON response
            listings = response.json()

            # Check if there are any results
            if not listings:
                await ctx.send(f"No listings found for '{query}' on CSFloat.")
                return

            # Dictionary to store lowest prices for each wear
            wear_prices = {
                'Factory New': None,
                'Minimal Wear': None,
                'Field-Tested': None,
                'Well-Worn': None,
                'Battle-Scarred': None
            }

            # Find the lowest price for each wear condition
            for listing in listings:
                item = listing.get('item', {})
                wear_name = item.get('wear_name', 'Unknown')
                price = listing.get('price', None)
                
                # Convert price from cents to dollars and cents format
                if price is not None:
                    price_dollars = price / 100.0  # Convert cents to dollars
                    if wear_name in wear_prices.keys():
                        if wear_prices[wear_name] is None or price_dollars < wear_prices[wear_name]:
                            wear_prices[wear_name] = price_dollars

            # Prepare the results message
            result_messages = []
            for wear, price in wear_prices.items():
                if price is not None:
                    result_messages.append(f"{wear}: ${price:.2f} USD")

            results_message = '\n'.join(result_messages)
            await ctx.send(f"Lowest prices for '{query}' on CSFloat:\n\n{results_message}")

        except requests.exceptions.RequestException as e:
            await ctx.send(f"An error occurred while fetching data from CSFloat: {e}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(CSFloatSearch(bot))
