from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command()
    async def kick(self, ctx, member: commands.MemberConverter):
        await member.kick()
        await ctx.send(f'{member.display_name} has been kicked.')

def setup(bot):
    bot.add_cog(Admin(bot))