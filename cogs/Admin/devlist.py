from discord.ext import commands
import discord
from itertools import groupby

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='devlist', aliases=['devcmds', 'devcommands'], help='Displays a list of all bot commands')
    async def commands_list(self, ctx):
        command_list = sorted([command.name for command in self.bot.commands])
        await ctx.message.delete()
        formatted_commands = []
        counter = 1
        
        for letter, cmds in groupby(command_list, key=lambda x: x[0].upper()):
            formatted_commands.append(f"\n**{letter.upper()}**")
            for cmd in cmds:
                formatted_commands.append(f"`{counter}`. {cmd}")
                counter += 1

        embed = discord.Embed(
            title="List of Every Single Command",
            description="\n".join(formatted_commands),
            color=discord.Color.gold()
        )

        message = await ctx.send(embed=embed)
        await message.delete(delay=60)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))
