import os
import discord
from discord.ext import commands
import asyncio

class LinksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="links")
    async def links(self, ctx: commands.Context):
        await ctx.message.delete()
        embed = self.create_links_embed()
        view = self.create_links_view()
        sent_message = await ctx.send(embed=embed, view=view)
        await asyncio.sleep(60)
        await sent_message.delete()

    def create_links_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Useful Links <:rosa:1323457812755644498>",
            description="Click the buttons below to open the corresponding link.",
            color=discord.Color.dark_red()
        )
        return embed

    def create_links_view(self) -> discord.ui.View:
        view = discord.ui.View()
        github_button = discord.ui.Button(
            label="GitHub",
            url="https://github.com/xyz-q"
        )
        view.add_item(github_button)
        reddit_button = discord.ui.Button(
            label="Reddit",
            url="https://www.reddit.com/user/mxttyyc/"
        )
        view.add_item(reddit_button)
        youtube_button = discord.ui.Button(
            label="TTV",
            url="https://www.twitch.tv/zxpqqq"
        )
        view.add_item(youtube_button)
        website_button = discord.ui.Button(
            label="Steam",
            url="https://steamcommunity.com/id/offdaperc_"
        )
        view.add_item(website_button)
        return view

async def setup(bot: commands.Bot):
    await bot.add_cog(LinksCog(bot))
