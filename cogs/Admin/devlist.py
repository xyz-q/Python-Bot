from discord.ext import commands
import discord
from itertools import groupby

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='devlist', aliases=['devcmds', 'devcommands'], help='Displays a list of all bot commands')
    async def commands_list(self, ctx):
        # Fetching all commands registered in the bot
        command_list = sorted([command.name for command in self.bot.commands])
        await ctx.message.delete()
        # Group commands by first letter and format with numbers
        formatted_commands = []
        counter = 1
        
        # Group by first letter
        for letter, cmds in groupby(command_list, key=lambda x: x[0].upper()):
            # Add letter header
            formatted_commands.append(f"\n**{letter.upper()}**")
            # Add numbered commands
            for cmd in cmds:
                formatted_commands.append(f"`{counter}`. {cmd}")
                counter += 1

        # Creating the embed
        embed = discord.Embed(
            title="List of Every Single Command",
            description="\n".join(formatted_commands),
            color=discord.Color.gold()
        )

        # Send the embed and delete it after 60 seconds
        message = await ctx.send(embed=embed)
        await message.delete(delay=60)

# Setup function to add the cog
async def setup(bot):
    await bot.add_cog(InfoCog(bot))
