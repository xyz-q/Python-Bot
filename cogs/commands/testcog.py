import discord
from discord.ext import commands
from discord import app_commands

class Testcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cog1", description="Sends hello!")
    async def cog1(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="Hello!")

async def setup(bot):
    await bot.add_cog(Testcog(bot))