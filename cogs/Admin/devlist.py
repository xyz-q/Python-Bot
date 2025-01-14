from discord.ext import commands
import discord

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='devlist', aliases=['devcmds', 'devcommands'], help='Displays a list of all bot commands')
    async def commands_list(self, ctx):
        # Fetching all commands registered in the bot
        command_list = [command.name for command in self.bot.commands]

        # Sorting the list alphabetically
        command_list.sort()

        # Creating the embed
        embed = discord.Embed(
            title="List of Available Commands",
            description="\n".join(command_list),
            color=discord.Color.blue()
        )

        # Send the embed and delete it after 45 seconds
        message = await ctx.send(embed=embed)
        await message.delete(delay=60)

# Setup function to add the cog
async def setup(bot):
    await bot.add_cog(InfoCog(bot))
