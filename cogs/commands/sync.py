import discord
from discord.ext import commands

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sync', description='Sync slash commands.')
    async def sync_slash_commands(self, ctx):
        await ctx.send("Syncing slash commands...")

        # Accessing the method from the main bot instance
        try:
            await self.bot.tree.sync()  # Assuming 'tree' is a method in your bot
            await ctx.send("Slash commands synchronized successfully!")
            print("Slash commands synchronized successfully!")
        except Exception as e:
            await ctx.send(f"Failed to sync slash commands: {e}")
            print(f"Failed to sync slash commands: {e}")

async def setup(bot):
    await bot.add_cog(Sync(bot))