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

    @commands.command(aliases=['cs2patch', 'cs2update'])
    async def cs2updates(self, ctx):
        """Get the latest CS2 patch notes from Steam"""
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

            # Filter for patch notes/updates (not just any news)
            patch_keywords = ['update', 'patch', 'release', 'notes', 'changelog']
            patch_item = None
            
            for item in data['appnews']['newsitems']:
                title = item.get('title', '').lower()
                if any(keyword in title for keyword in patch_keywords):
                    patch_item = item
                    break
            
            if not patch_item:
                patch_item = data['appnews']['newsitems'][0]  # Fallback to latest

            title = patch_item.get('title', 'No Title')
            contents = patch_item.get('contents', 'No content available')
            date = datetime.fromtimestamp(patch_item.get('date', 0))
            url = patch_item.get('url', '')
            
            # Clean up content
            import re
            clean_content = re.sub('<[^<]+?>', '', contents)
            if len(clean_content) > 800:
                clean_content = clean_content[:800] + "..."

            embed = discord.Embed(
                title=f"🔧 {title}",
                description=clean_content,
                color=0xF7931E,
                url=url
            )
            
            embed.add_field(
                name="📅 Release Date",
                value=date.strftime('%B %d, %Y at %H:%M UTC'),
                inline=True
            )
            
            embed.set_footer(text="Latest CS2 Patch Notes from Steam", icon_url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching CS2 updates: {str(e)}")

async def setup(bot):
    await bot.add_cog(CS2Updates(bot))