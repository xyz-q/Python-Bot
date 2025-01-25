import discord
from discord.ext import commands

class DowntimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='downtime')
    @commands.is_owner()
    async def downtime(self, ctx):
        downtime_message = "The bot will be offline for a bit. Please check the status to see when I put it back online"

        for guild in self.bot.guilds:
            owner = guild.owner
            try:
                await owner.send(downtime_message)
                await ctx.send(f"Downtime message sent to the owner of {guild.name}")
            except discord.HTTPException:
                await ctx.send(f"Unable to send downtime message to the owner of {guild.name}")

        await ctx.send("Downtime message sent to all server owners.")

async def setup(bot):
    await bot.add_cog(DowntimeCog(bot))
