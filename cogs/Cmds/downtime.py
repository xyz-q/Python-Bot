import discord
from discord.ext import commands

class DowntimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='downtime')
    @commands.is_owner()
    async def downtime(self, ctx):
        downtime_message = "Hello, this is an automated message to inform you that I will be going for downtime for maintenance purposes. During this time, I may be unavailable or experience some disruptions in service. Thank you for your understanding."

        for guild in self.bot.guilds:
            owner = guild.owner
            try:
                await owner.send(downtime_message)
                await ctx.send(f"Downtime message sent to the owner of {guild.name}")
            except discord.HTTPException:
                await ctx.send(f"Unable to send downtime message to the owner of {guild.name}")

        await ctx.send("Downtime messages sent to all server owners.")

async def setup(bot):
    await bot.add_cog(DowntimeCog(bot))
