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
        
        await interaction.response.send_message("Sending messages to all channels...", ephemeral=True)
        
        all_channels = interaction.guild.channels
        text_channels = interaction.guild.text_channels
        total_channels = len(text_channels)
        sent_count = 0
        failed_channels = []
        
        print(f"Total channels: {len(all_channels)}, Text channels: {len(text_channels)}")
        for ch in all_channels:
            print(f"Channel: {ch.name} - Type: {type(ch)}")
        
        for channel in text_channels:
            if channel.permissions_for(interaction.guild.me).send_messages:
                try:
                    for _ in range(times):
                        await channel.send(message)
                    sent_count += 1
                except (discord.Forbidden, discord.HTTPException) as e:
                    failed_channels.append(f"{channel.name}: {str(e)}")
                    continue
            else:
                failed_channels.append(f"{channel.name}: No send permission")
        
        result = f"✅ Sent to {sent_count}/{total_channels} channels {times} time(s) each."
        if failed_channels:
            result += f"\n\n❌ Failed channels:\n" + "\n".join(failed_channels[:5])
            if len(failed_channels) > 5:
                result += f"\n...and {len(failed_channels) - 5} more"
        
        await interaction.followup.send(result, ephemeral=True)
        print("\033[95mUser has used a /slash command.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageAll(bot))