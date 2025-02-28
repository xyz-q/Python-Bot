import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Store webhook URLs in environment variables for security
LIGHT_ON_WEBHOOK = os.getenv("LIGHT_ON_WEBHOOK")
LIGHT_OFF_WEBHOOK = os.getenv("LIGHT_OFF_WEBHOOK")

class LightControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("LightControl cog is ready!")
        # Get the channel where you want to post the embed
        channel_id = int(os.getenv("LIGHT_CONTROL_CHANNEL_ID"))
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            # Clear all messages in the channel
            await channel.purge(limit=None)
            
            # Create the embed
            embed = discord.Embed(
                title="Light Control Panel",
                description="Control your lights with the buttons below",
                color=discord.Color.blue()
            )
            
            # Create view with buttons
            view = LightControlView()
            
            # Send the embed with buttons
            await channel.send(embed=embed, view=view)

class LightControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view that doesn't timeout
    
    @discord.ui.button(label="Light ON", style=discord.ButtonStyle.green, custom_id="light_on")
    async def light_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(LIGHT_ON_WEBHOOK) as response:
                    if response.status == 200:
                        await interaction.response.send_message("Light turned ON!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Failed to turn light ON. Status: {response.status}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Light OFF", style=discord.ButtonStyle.red, custom_id="light_off")
    async def light_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(LIGHT_OFF_WEBHOOK) as response:
                    if response.status == 200:
                        await interaction.response.send_message("Light turned OFF!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Failed to turn light OFF. Status: {response.status}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LightControl(bot))
