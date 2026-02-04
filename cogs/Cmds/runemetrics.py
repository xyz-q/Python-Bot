import discord
from discord.ext import commands
import aiohttp
import re
from bs4 import BeautifulSoup

class RuneMetrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='drops')
    async def check_drops(self, ctx, username: str = "R0SA+PERCS"):
        url = f"https://apps.runescape.com/runemetrics/app/activities/player/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Debug: Print first 1000 chars of HTML
                        print(f"HTML Preview: {html[:1000]}")
                        
                        # Look for "I found" in the raw HTML
                        found_items = re.findall(r'I found [^<]+', html, re.IGNORECASE)
                        
                        if found_items:
                            embed = discord.Embed(
                                title=f"Recent Drops - {username}",
                                color=discord.Color.gold()
                            )
                            
                            for item in found_items[:10]:  # Limit to 10 items
                                embed.add_field(
                                    name="Drop",
                                    value=item,
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