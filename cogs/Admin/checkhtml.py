import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup

class CheckHTML(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        return ctx.author.id == 110927272210354176

    @commands.command(name='checkhtml')
    async def check_html(self, ctx, url: str, *, search_term: str = None):
        """Check HTML structure of any website and optionally search for content"""
        
        # Add https:// if not present
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        embed = discord.Embed(
            title="🔍 Fetching HTML...",
            description=f"Analyzing: {url}",
            color=0xffff00
        )
        message = await ctx.send(embed=embed)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            embed = discord.Embed(
                title="📄 HTML Analysis",
                description=f"**URL:** {url}",
                color=0x00ff00
            )
            
            # Basic structure info
            scripts = soup.find_all('script')
            divs = soup.find_all('div')
            links = soup.find_all('a')
            
            embed.add_field(
                name="Structure",
                value=f"Scripts: {len(scripts)}\nDivs: {len(divs)}\nLinks: {len(links)}",
                inline=True
            )
            
            # If search term provided
            if search_term:
                found_in = []
                
                # Search in script tags
                for i, script in enumerate(scripts):
                    if script.string and search_term in script.string:
                        found_in.append(f"Script[{i}]")
                
                # Search in raw HTML
                if search_term in html_content:
                    found_in.append("Raw HTML")
                
                if found_in:
                    embed.add_field(
                        name=f"Search: '{search_term}'",
                        value=f"Found in: {', '.join(found_in)}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Search: '{search_term}'",
                        value="Not found",
                        inline=False
                    )
            
            # Show script previews
            script_info = ""
            for i, script in enumerate(scripts[:5]):
                if script.string:
                    preview = script.string[:100].replace('\n', ' ')
                    script_info += f"[{i}] {preview}...\n"
                else:
                    script_info += f"[{i}] (external/empty)\n"
            
            if len(scripts) > 5:
                script_info += f"... and {len(scripts) - 5} more scripts"
            
            if script_info:
                embed.add_field(
                    name="Script Preview",
                    value=f"```{script_info}```",
                    inline=False
                )
            
            await message.edit(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to fetch HTML: {str(e)}",
                color=0xff0000
            )
            await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(CheckHTML(bot))