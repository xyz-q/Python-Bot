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

WEAR_CONDITIONS = ['Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred']
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
        self.listings_url = 'https://csfloat.com/api/v1/listings'
        self.api_key = os.getenv('CSFLOAT_API_KEY', '')

    @property
    def _headers(self):
        return {'Authorization': self.api_key} if self.api_key else {}

    async def skin_autocomplete(self, interaction: Interaction, current: str):
        weapon = interaction.namespace.weapon or ''
        query = f"{weapon} | {current}" if weapon else current
        if len(query.strip()) < 2:
            return []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://csfloat.com/api/v1/meta/search',
                    params={'query': query, 'limit': 25},
                    headers=self._headers
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    items = data if isinstance(data, list) else data.get('data', [])
                    skins = []
                    for item in items:
                        name = item.get('market_hash_name', '')
                        if ' | ' in name:
                            skin_part = name.split(' | ', 1)[1].split(' (')[0]
                            skins.append(app_commands.Choice(name=skin_part[:100], value=skin_part))
                    return skins[:25]
        except Exception:
            return []

    @app_commands.command(name="price", description="Look up lowest CSFloat prices for a CS2 skin")
    @app_commands.autocomplete(weapon=weapon_autocomplete, skin=skin_autocomplete, wear=wear_autocomplete, skin_type=skin_type_autocomplete)
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

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.listings_url, params=params, headers=self._headers) as resp:
                    if resp.status == 403:
                        await interaction.followup.send("CSFloat API returned 403 — check your API key.", ephemeral=True)
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

            if not any(wear_prices.values()):
                await interaction.followup.send(f"No priced listings found for `{query}`.", ephemeral=True)
                return

            lowest = min(p for p in wear_prices.values() if p is not None)
            thumbnail = None
            for listing in listings:
                img = listing.get('item', {}).get('icon_url') or listing.get('item', {}).get('image_url')
                if img:
                    thumbnail = img if img.startswith('http') else f"https://steamcommunity-a.akamaihd.net/economy/image/{img}"
                    break

            embed = discord.Embed(
                title=query,
                description=f"Lowest available: **${lowest:.2f} USD**",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            for w in WEAR_CONDITIONS:
                if wear_prices[w] is not None:
                    embed.add_field(name=w, value=f"${wear_prices[w]:.2f} USD", inline=True)
            embed.set_footer(text="Powered by CSFloat")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CSFloatSearch2(bot))
