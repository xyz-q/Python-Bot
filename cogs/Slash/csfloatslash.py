import discord
from discord.ext import commands
from discord import app_commands, Interaction
import aiohttp
import os

WEAPON_NAMES = [
    '★ Karambit', '★ Bayonet', '★ M9 Bayonet', '★ Flip Knife', '★ Gut Knife',
    '★ Bowie Knife', '★ Butterfly Knife', '★ Shadow Daggers', '★ Huntsman Knife',
    '★ Falchion Knife', '★ Ursus Knife', '★ Navaja Knife', '★ Stiletto Knife',
    '★ Talon Knife', '★ Classic Knife', '★ Nomad Knife', '★ Skeleton Knife',
    '★ Sport Gloves', '★ Moto Gloves', '★ Hand Wraps', '★ Driver Gloves',
    '★ Specialist Gloves', '★ Bloodhound Gloves', '★ Hydra Gloves', '★ Broken Fang Gloves',
    'Glock-18', 'USP-S', 'P2000', 'Dual Berettas', 'P250', 'Tec-9', 'Five-SeveN',
    'CZ75-Auto', 'Desert Eagle', 'R8 Revolver', 'Nova', 'XM1014', 'Sawed-Off', 'MAG-7',
    'M249', 'Negev', 'MP9', 'MAC-10', 'MP7', 'UMP-45', 'P90', 'PP-Bizon',
    'AK-47', 'M4A4', 'M4A1-S', 'Galil AR', 'FAMAS', 'SG 553', 'AUG',
    'AWP', 'G3SG1', 'SCAR-20', 'SSG 08', 'Zeus x27'
]

WEAR_CONDITIONS = ['Battle-Scarred', 'Well-Worn', 'Field-Tested', 'Minimal Wear', 'Factory New']
SKIN_TYPES = ['StatTrak™', 'Souvenir']


async def weapon_autocomplete(interaction: Interaction, current: str):
    return [app_commands.Choice(name=w, value=w) for w in WEAPON_NAMES if current.lower() in w.lower()][:25]

async def wear_autocomplete(interaction: Interaction, current: str):
    return [app_commands.Choice(name=w, value=w) for w in WEAR_CONDITIONS if current.lower() in w.lower()][:25]

async def skin_type_autocomplete(interaction: Interaction, current: str):
    return [app_commands.Choice(name=s, value=s) for s in SKIN_TYPES if current.lower() in s.lower()][:25]


class CSFloatSearch2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = 'https://csfloat.com/api/v1/listings'
        self.api_key = os.getenv('CSFLOAT_API_KEY', '')

    @app_commands.command(name="price", description="Look up lowest CSFloat prices for a CS2 skin")
    @app_commands.autocomplete(weapon=weapon_autocomplete, wear=wear_autocomplete, skin_type=skin_type_autocomplete)
    @app_commands.describe(
        weapon="The CS2 weapon",
        skin="The skin name",
        wear="The wear condition",
        skin_type="StatTrak™ or Souvenir (leave empty for normal)"
    )
    async def price(self, interaction: Interaction, weapon: str, skin: str, wear: str, skin_type: str = ""):
        await interaction.response.defer()

        if weapon.startswith('★'):
            query = f"★ {skin_type} {weapon[2:]} | {skin} ({wear})" if skin_type else f"{weapon} | {skin} ({wear})"
        else:
            query = f"{skin_type + ' ' if skin_type else ''}{weapon} | {skin} ({wear})"

        params = {'market_hash_name': query, 'sort_by': 'lowest_price', 'limit': 50}
        headers = {'Authorization': self.api_key} if self.api_key else {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params, headers=headers) as resp:
                    if resp.status == 403:
                        await interaction.followup.send("CSFloat API returned 403 — an API key is required. Set `CSFLOAT_API_KEY` in your environment.", ephemeral=True)
                        return
                    if resp.status != 200:
                        await interaction.followup.send(f"CSFloat API error: HTTP {resp.status}", ephemeral=True)
                        return
                    data = await resp.json()
                    listings = data.get('data', data) if isinstance(data, dict) else data

            if not listings:
                await interaction.followup.send(f"No listings found for `{query}`.", ephemeral=True)
                return

            wear_prices = {w: None for w in WEAR_CONDITIONS}
            for listing in listings:
                item = listing.get('item', {})
                wear_name = item.get('wear_name')
                price_cents = listing.get('price')
                if wear_name in wear_prices and price_cents is not None:
                    price_dollars = price_cents / 100.0
                    if wear_prices[wear_name] is None or price_dollars < wear_prices[wear_name]:
                        wear_prices[wear_name] = price_dollars

            embed = discord.Embed(title=f"Lowest prices for {query}", color=0xFF0000)
            for w, p in wear_prices.items():
                if p is not None:
                    embed.add_field(name=w, value=f"${p:.2f} USD", inline=False)

            if not any(wear_prices.values()):
                await interaction.followup.send(f"No priced listings found for `{query}`.", ephemeral=True)
                return

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CSFloatSearch2(bot))
