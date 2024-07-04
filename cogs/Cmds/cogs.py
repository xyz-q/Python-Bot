import discord
from discord.ext import commands
import asyncio

class CogLister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='listcogs', aliases=['cogs'])
    async def listcogs(self, ctx):
        await ctx.message.delete()
        cogs = self.bot.cogslist
        cog_chunks = [cogs[i:i+8] for i in range(0, len(cogs), 8)]
        max_pages = len(cog_chunks)

        class CogView(discord.ui.View):
            def __init__(self, ctx, cog_chunks):
                super().__init__(timeout=15)
                self.ctx = ctx
                self.cog_chunks = cog_chunks
                self.current_page = 0
                self.message = None

            async def on_timeout(self):
                if self.message:
                    await self.message.delete()

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()  # Defer the interaction
                if interaction.user != self.ctx.author:
                    return
                self.current_page = max(0, self.current_page - 1)
                await self.update_embed()

            @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()  # Defer the interaction
                if interaction.user != self.ctx.author:
                    return
                self.current_page = min(max_pages - 1, self.current_page + 1)
                await self.update_embed()

            @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
            async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()  # Defer the interaction
                if interaction.user != self.ctx.author:
                    return
                await self.message.delete()
                self.stop()

            async def update_embed(self):
                embed = discord.Embed(title="Cog List", color=discord.Color.red())
                embed.add_field(name=f"Page {self.current_page+1}/{max_pages}", value="\n".join(self.cog_chunks[self.current_page]), inline=False)
                self.previous.disabled = self.current_page == 0
                self.next.disabled = self.current_page == max_pages - 1
                if self.message:
                    await self.message.edit(embed=embed, view=self)
                else:
                    self.message = await self.ctx.send(embed=embed, view=self)

        view = CogView(ctx, cog_chunks)
        await view.update_embed()
        await view.wait()

async def setup(bot):
    await bot.add_cog(CogLister(bot))
