import aiohttp
from discord.ext import commands
import asyncio

# Global variable for aiohttp session
session = None

class AiohttpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command to force shutdown aiohttp session
    @commands.command(name='shutdown')
    async def shutdown(self, ctx):
        global session
        if session:
            await session.close()
            session = None
            await ctx.send("aiohttp session closed.")
        else:
            await ctx.send("No active aiohttp session.")

async def setup(bot):
    global session
    if session is None:
        session = aiohttp.ClientSession()
    await bot.add_cog(AiohttpCommands(bot))

def teardown(bot):
    global session
    if session:
        loop = bot.loop
        asyncio.ensure_future(session.close(), loop=loop)
        session = None
