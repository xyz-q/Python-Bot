import os
import discord
from discord.ext import commands
import webbrowser
import asyncio

# Discord API credentials
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")

class InviteCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        await ctx.message.delete()
        oauth2_url = self.generate_oauth2_url()
        webbrowser.open(oauth2_url)
        invite_message = await ctx.send("The invite page has been opened in your default browser!")

        await asyncio.sleep(5)
        await invite_message.delete()

    def generate_oauth2_url(self):
        url = f"https://discord.com/oauth2/authorize?client_id=1233966655923552370&permissions=8&integration_type=0&scope=applications.commands+bot"
        return url

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteCommand(bot))