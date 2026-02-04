import discord
from discord.ext import commands
import aiohttp
import json

class RuneMetrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='drops')
    async def check_drops(self, ctx, username: str = "R0SA+PERCS"):
        # Use the RuneMetrics API directly
        api_url = f"https://apps.runescape.com/runemetrics/profile/profile?user={username}&activities=20"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        activities = data.get('activities', [])
                        found_items = []
                        
                        for activity in activities:
                            text = activity.get('text', '')
                            if text.lower().startswith('i found'):
                                found_items.append({
                                    'text': text,
                                    'date': activity.get('date')
                                })
                        
                        if found_items:
                            embed = discord.Embed(
                                title=f"Recent Drops - {username}",
                                color=discord.Color.gold()
                            )
                            
                            for item in found_items[:10]:  # Limit to 10 items
                                embed.add_field(
                                    name="Drop",
                                    value=f"{item['text']} ({item['date']})",
                                    inline=False
                                )
                            
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send(f"No recent drops found for {username}")
                    else:
                        await ctx.send(f"Error fetching data: Status {response.status}")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

async def setup(bot):
    await bot.add_cog(RuneMetrics(bot))