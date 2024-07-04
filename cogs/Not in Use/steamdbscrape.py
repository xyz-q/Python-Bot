import discord
from discord.ext import commands
import requests

class SteamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = 'C65FA00D562B57B6E29F168649BF639D'  # Replace with your Steam Web API key

    @commands.command(name='depot_changes')
    async def fetch_depot_changes(self, ctx):
        # Endpoint for getting depot changes for CS:GO
        endpoint = f'http://api.steampowered.com/ISteamApps/GetDepotChanges/v1/?appid=730&depotid=730&maxcount=5&key={self.api_key}'

        try:
            response = requests.get(endpoint)

            if response.status_code == 200:
                data = response.json()
                changes = data.get('depot_change_data', [])
                
                if changes:
                    changes_message = "\n".join([f"Date: {change['time']}, Change: {change['change_description']}" for change in changes])
                    await ctx.send(f"Latest Depot Changes:\n{changes_message}")
                else:
                    await ctx.send("No changes found in the depot.")
            else:
                await ctx.send(f"Failed to fetch depot changes. HTTP status code: {response.status_code}")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(SteamCog(bot))
