import discord
from discord.ext import commands
from functools import wraps
import asyncio

class CommandLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_locks = {}

    def user_command_lock():
        """
        Decorator that prevents a user from running any command while they have one running
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, ctx, *args, **kwargs):
                user_id = ctx.author.id
                
                if user_id in self.user_locks and self.user_locks[user_id]:
                    await ctx.send(f"{ctx.author.mention}, please wait for your current command to finish!")
                    return

                try:
                    self.user_locks[user_id] = True
                    return await func(self, ctx, *args, **kwargs)
                finally:
                    self.user_locks[user_id] = False
                    
            return wrapper
        return decorator

    @commands.command()
    @user_command_lock()
    async def long_task(self, ctx):
        await ctx.send(f"{ctx.author.mention} starting a long task...")
        await asyncio.sleep(5)
        await ctx.send(f"{ctx.author.mention} long task completed!")

    @commands.command()
    @user_command_lock()
    async def another_task(self, ctx):
        await ctx.send(f"{ctx.author.mention} starting another task...")
        await asyncio.sleep(3)
        await ctx.send(f"{ctx.author.mention} another task completed!")

async def setup(bot):
    await bot.add_cog(CommandLock(bot))
