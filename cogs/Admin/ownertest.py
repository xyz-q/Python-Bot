import discord
from discord.ext import commands

class OwnerTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="testowner")
    @commands.is_owner()
    async def test_owner(self, ctx):
        """Test command to verify @commands.is_owner() works"""
        await ctx.send(f"✅ @commands.is_owner() works! You are recognized as the bot owner.")
        await ctx.send(f"Your ID: {ctx.author.id}")
        await ctx.send(f"Bot owner ID from application: {self.bot.owner_id}")

    @commands.command(name="whoowner")
    async def who_owner(self, ctx):
        """Shows who the bot thinks is the owner"""
        owner = self.bot.get_user(self.bot.owner_id)
        await ctx.send(f"Bot owner: {owner.mention if owner else 'Unknown'} (ID: {self.bot.owner_id})")
        await ctx.send(f"Your ID: {ctx.author.id}")
        await ctx.send(f"Are you owner? {ctx.author.id == self.bot.owner_id}")

async def setup(bot):
    await bot.add_cog(OwnerTest(bot))