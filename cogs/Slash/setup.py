import discord
from discord.ext import commands
from discord import app_commands

class Setuphelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Shows user how to setup the bot properly.")
    async def setup(self, interaction: discord.Interaction):
        help_message = (
            "To set up the bot with your server, you need to:\n"
            "1. Create a role named `.trusted`\n"
            "2. Create a text channel named `admin-commands`\n"
            "3. Also create a text channel named `tickets`\n\n"
            "After that, you can execute commands in the `admin-commands` channel.\n\n"
            "Note: You must have the role `.trusted` in order to process commands, the command prefix is ','"
        )
        await interaction.response.send_message(content=help_message, ephemeral=True)
        print("\033[95mUser has used a /slash command.")
        
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Setuphelp(bot))
    