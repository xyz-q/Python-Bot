import discord
from discord.ext import commands
import random

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='coinflip', aliases=['cf2',])
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="Coin Flip",
            description=f"The coin landed on: **{result}**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://image.shutterstock.com/image-vector/coin-flip-heads-tails-icons-260nw-1924849807.jpg")  # Example URL for coin image
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
