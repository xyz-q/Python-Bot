import discord
from discord.ext import commands
import aiohttp

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3.1:8b"

    @commands.command()
    async def ai(self, ctx, *, prompt):
        """Ask the local AI a question"""

        async with ctx.typing():

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.ollama_url,
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False
                        }
                    ) as response:

                        data = await response.json()
                        answer = data["response"]

            except Exception as e:
                await ctx.send(f"AI error: {e}")
                return

        if len(answer) > 1900:
            answer = answer[:1900] + "..."

        await ctx.send(answer)

async def setup(bot):
    await bot.add_cog(AI(bot))