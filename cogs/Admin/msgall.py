import discord
from discord.ext import commands
from discord import app_commands

class MessageAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @app_commands.command(name="msgall", description="Send a message to all channels")
    @app_commands.describe(message="The message to send", times="Number of times to send (default: 1)")
    async def msgall(self, interaction: discord.Interaction, message: str, times: int = 1):
        try:
            times = min(times, 10)
            
            await interaction.response.send_message("Processing...", ephemeral=True)
            
            if not interaction.guild or not interaction.guild.me:
                await interaction.followup.send("❌ Error: Cannot access guild information!", ephemeral=True)
                return
            
            # Get channels the bot can actually see
            text_channels = [ch for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)]
            total_channels = len(text_channels)
            
            if total_channels == 0:
                await interaction.followup.send("❌ No text channels found! Bot may need 'View Channels' permission.", ephemeral=True)
                return
            
            sent_count = 0
            failed_channels = []
            
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
            
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                print(f"Failed to send error message: {e}")
        print("\033[95mUser has used a /slash command.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageAll(bot))