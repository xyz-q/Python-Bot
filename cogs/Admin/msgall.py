import discord
from discord.ext import commands
from discord import app_commands

class MessageAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="msgall", description="Send a message to all channels")
    @app_commands.describe(message="The message to send", times="Number of times to send (default: 1)")
    async def msgall(self, interaction: discord.Interaction, message: str, times: int = 1):
        times = min(times, 10)
        
        sent_count = 0
        for channel in interaction.guild.text_channels:
            if channel.permissions_for(interaction.guild.me).send_messages:
                try:
                    for _ in range(times):
                        await channel.send(message)
                    sent_count += 1
                except discord.Forbidden:
                    continue
        
        await interaction.response.send_message(f"Message sent to {sent_count} channels {times} time(s) each.", ephemeral=True)
        print("\033[95mUser has used a /slash command.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageAll(bot))