
import os
import discord
from discord.ext import commands
import asyncio

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")

class InviteCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        await ctx.message.delete()
        oauth2_url = self.generate_oauth2_url()
        
        embed = discord.Embed(
            title="Bot Invite Link",
            description="Click the button below to invite the bot to your server.",
            color=discord.Color.gold()
        )

        button = discord.ui.Button(label="Invite Bot", url=oauth2_url)

        view = discord.ui.View()
        view.add_item(button)

        invite_message = await ctx.send(embed=embed, view=view)
        await asyncio.sleep(15)  # Keep the message for 15 seconds before deleting
        await invite_message.delete()

    def generate_oauth2_url(self):
        url = f"https://discord.com/oauth2/authorize?client_id=1233966655923552370&permissions=8&integration_type=0&scope=applications.commands+bot"
        return url

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteCommand(bot))    