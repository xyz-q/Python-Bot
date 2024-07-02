import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import requests

WEAPON_NAMES = [
    '★ Karambit', '★ Bayonet', '★ M9 Bayonet', '★ Flip Knife', '★ Gut Knife',
    '★ Bowie Knife', '★ Butterfly Knife', '★ Shadow Daggers', '★ Huntsman Knife',
    '★ Falchion Knife', '★ Shadow Daggers', '★ Ursus Knife', '★ Navaja Knife', '★ Stiletto Knife',
    '★ Talon Knife', '★ Classic Knife', '★ Nomad Knife', '★ Skeleton Knife', '★ Sport Gloves', '★ Moto Gloves', '★ Hand Wraps', '★ Driver Gloves', '★ Specialist Gloves', '★ Bloodhound Gloves', '★ Hydra Gloves', '★ Broken Fang Gloves',
    'Glock-18', 'USP-S', 'P2000', 'Dual Berettas', 'P250', 'Tec-9',
    'Five-SeveN', 'CZ75-Auto', 'Desert Eagle', 'R8 Revolver', 'Nova',
    'XM1014', 'Sawed-Off', 'MAG-7', 'M249', 'Negev', 'MP9', 'MAC-10',
    'MP7', 'UMP-45', 'P90', 'PP-Bizon', 'AK-47', 'M4A4', 'M4A1-S',
    'Galil AR', 'FAMAS', 'SG 553', 'AUG', 'AWP', 'G3SG1', 'SCAR-20',
    'SSG 08', 'Zeus x27'
]

WEAR_CONDITIONS = [
    'Battle-Scarred', 'Well-Worn', 'Field-Tested', 'Minimal Wear', 'Factory New'
]

SKIN_TYPES = ['StatTrak™', 'Souvenir']

async def weapon_autocomplete(interaction: Interaction, current: str):
    return [
        app_commands.Choice(name=weapon, value=weapon)
        for weapon in WEAPON_NAMES
        if current.lower() in weapon.lower()
    ][:25]

async def wear_autocomplete(interaction: Interaction, current: str):
    return [
        app_commands.Choice(name=wear, value=wear)
        for wear in WEAR_CONDITIONS
        if current.lower() in wear.lower()
    ][:25]

async def skin_type_autocomplete(interaction: Interaction, current: str):
    return [
        app_commands.Choice(name=skin_type, value=skin_type)
        for skin_type in SKIN_TYPES
        if current.lower() in skin_type.lower()
    ][:25]

class CSFloatSearch2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = 'https://csfloat.com/api/v1/listings'

    @app_commands.command(description="Get a CS2 skin price from CSFloat.com")
    @app_commands.autocomplete(weapon=weapon_autocomplete)
    @app_commands.autocomplete(wear=wear_autocomplete)
    @app_commands.autocomplete(skin_type=skin_type_autocomplete)
    @app_commands.describe(
        weapon="The CS2 weapon",
        skin="The skin name",
        wear="The wear condition of the item",
        skin_type="The type of skin (Normal, StatTrak, or Souvenir). Leave empty for Normal."
    )
    async def price(self, interaction: Interaction, weapon: str, skin: str, wear: str, skin_type: str = ""):
        query = f"{skin_type + ' ' if skin_type else ''}{weapon} | {skin} ({wear})"
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
                await interaction.response.send_message(f"No listings found for '{query}' on CSFloat. Are you sure the name is correct? There could also be a float cap.", ephemeral=True)
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

            # Prepare the embed message
            embed = discord.Embed(title=f"Lowest prices for {query} on CSFloat", color=0xFF0000)
            for wear, price in wear_prices.items():
                if price is not None:
                    embed.add_field(name=wear, value=f"${price:.2f} USD", inline=False)

            await interaction.response.send_message(embed=embed)

        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(f"An error occurred while fetching data from CSFloat: {e}")
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(CSFloatSearch2(bot))
