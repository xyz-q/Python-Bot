import discord
from discord.ext import commands
import asyncio
import sys

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kill(self, ctx):
        if ctx.author.id == 110927272210354176:
            class KillView(discord.ui.View):
                def __init__(self, ctx):
                    super().__init__(timeout=10.0)
                    self.ctx = ctx
                    self.message = None

                async def on_timeout(self):
                    if self.message:
                        await self.message.edit(content=":clock1:  Bot TERMINATION cancelled due to inactivity.", view=None)
                        print("Bot termination CANCELLED from inactivity")
                        self.stop()

                @discord.ui.button(label="Terminate", style=discord.ButtonStyle.danger)
                async def terminate(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.defer()
                    if interaction.user != self.ctx.author:
                        return
                    terminated_message = await self.message.edit(content=":warning: Bot instance(s) TERMINATED.", view=None)
                    print(f"\033[96mBOT HAS BEEN TERMINATED BY: {self.ctx.author.name} ({self.ctx.author.id})\033[0m")
                    guild = self.ctx.bot.get_guild(1056994840925192252)
                    channel = discord.utils.get(guild.text_channels, name="bot-status")
                    if channel:
                        await channel.send(":red_circle: xyz is now offline [Killed]")
                    self.stop()
                    await self.ctx.bot.close()
                    sys.exit()  
                    
                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.primary)
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.defer()
                    if interaction.user != self.ctx.author:
                        return
                    await self.message.edit(content=" :orange_circle: Bot TERMINATION cancelled.", view=None)
                    print("Bot termination CANCELLED")
                    self.stop()

            view = KillView(ctx)
            warning_message = await ctx.send(":warning: Are you sure you want to TERMINATE the bot? This action cannot be undone.", view=view)
            view.message = warning_message
            await view.wait()
        else:
            await ctx.send(f":warning: [ERROR] {ctx.author.mention} is not permitted to operate this command.")
            print(f"\033[96mUSER TRYING TO KILL BOT: {ctx.author.name} ({ctx.author.id})\033[0m")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
