import discord
from discord.ext import commands
import aiohttp
import feedparser
from datetime import datetime

class CS2Updates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs2_app_id = "730"  # CS2's Steam app ID
        self.steam_news_url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={self.cs2_app_id}&count=5&maxlength=300&format=json"

    @commands.command(aliases=['cs2news', 'cs2update'])
    async def cs2updates(self, ctx):
        """Get the latest CS2 updates from Steam"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.steam_news_url) as response:
                    if response.status != 200:
                        await ctx.send("❌ Failed to fetch CS2 updates from Steam.")
                        return
                    
                    data = await response.json()
                    
            if not data.get('appnews', {}).get('newsitems'):
                await ctx.send("❌ No CS2 updates found.")
                return

            embed = discord.Embed(
                title="🎮 Counter-Strike 2 - Latest Updates",
                color=0xF7931E,  # Steam orange color
                url="https://store.steampowered.com/app/730/CounterStrike_2/"
            )
            
            news_items = data['appnews']['newsitems'][:3]  # Show top 3 updates
            
            for item in news_items:
                title = item.get('title', 'No Title')
                contents = item.get('contents', 'No content available')
                date = datetime.fromtimestamp(item.get('date', 0))
                url = item.get('url', '')
                
                # Clean up content (remove HTML tags and limit length)
                import re
                clean_content = re.sub('<[^<]+?>', '', contents)
                if len(clean_content) > 200:
                    clean_content = clean_content[:200] + "..."
                
                embed.add_field(
                    name=f"📰 {title}",
                    value=f"{clean_content}\n\n**Date:** {date.strftime('%B %d, %Y')}\n[Read More]({url})",
                    inline=False
                )
            
            embed.set_footer(text="Updates from Steam", icon_url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching CS2 updates: {str(e)}")

async def setup(bot):
    await bot.add_cog(CS2Updates(bot))