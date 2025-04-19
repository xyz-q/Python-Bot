import discord
from discord.ext import commands

class ErrorTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def divide_by_zero(self, ctx):
        """Raises a ZeroDivisionError"""
        result = 1 / 0

    @commands.command()
    async def type_error(self, ctx):
        """Raises a TypeError"""
        text = "hello"
        result = text + 123

    @commands.command()
    async def index_error(self, ctx):
        """Raises an IndexError"""
        my_list = [1, 2, 3]
        result = my_list[10]

    @commands.command()
    async def key_error(self, ctx):
        """Raises a KeyError"""
        my_dict = {"a": 1}
        result = my_dict["nonexistent_key"]

    @commands.command()
    async def value_error(self, ctx):
        """Raises a ValueError"""
        result = int("not a number")

    @commands.command()
    async def attribute_error(self, ctx):
        """Raises an AttributeError"""
        none_value = None
        result = none_value.something()

    @commands.command()
    async def permission_error(self, ctx):
        """Raises a discord.Forbidden error"""
        # Attempts to ban a user without proper permissions
        await ctx.guild.ban(ctx.author)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def check_fail(self, ctx):
        """Raises a CheckFailure if user is not admin"""
        await ctx.send("If you see this, you're an admin!")

async def setup(bot):
    await bot.add_cog(ErrorTest(bot))
