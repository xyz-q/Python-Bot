import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from dotenv import load_dotenv
import logging
from datetime, import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('light_control')

# Load environment variables
load_dotenv()

# Store webhook URLs in environment variables for security
LIGHT_ON_WEBHOOK = os.getenv("LIGHT_ON_WEBHOOK")
LIGHT_OFF_WEBHOOK = os.getenv("LIGHT_OFF_WEBHOOK")
CHANNEL_ID = os.getenv("LIGHT_CONTROL_CHANNEL_ID")

class LightControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_complete = False
        
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("LightControl cog on_ready event triggered")
        
        # Avoid running setup multiple times if on_ready fires more than once
        if self.setup_complete:
            return
            
        # Create a task to set up the control panel
        self.bot.loop.create_task(self.setup_control_panel())
        
    async def setup_control_panel(self):
        try:
            logger.info("Setting up light control panel")
            
            # Get the channel where you want to post the embed
            if not CHANNEL_ID:
                logger.error("No channel ID provided in environment variables")
                return
                
            channel_id = int(CHANNEL_ID)
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.error(f"Could not find channel with ID {channel_id}")
                # Try fetching the channel if get_channel fails
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception as e:
                    logger.error(f"Failed to fetch channel: {e}")
                    return
            
            logger.info(f"Found channel: {channel.name} (ID: {channel.id})")
            
            # Check permissions
            bot_member = channel.guild.get_member(self.bot.user.id)
            permissions = channel.permissions_for(bot_member)
            
            if not permissions.send_messages:
                logger.error("Bot doesn't have permission to send messages in this channel")
                return
                
            if not permissions.manage_messages:
                logger.warning("Bot doesn't have permission to delete messages in this channel")
            else:
                # Clear all messages in the channel
                logger.info("Purging channel messages")
                try:
                    await channel.purge(limit=100)  # Limit to 100 messages for safety
                    logger.info("Channel purged successfully")
                except Exception as e:
                    logger.error(f"Error purging channel: {e}")
            
            # Create the embed
            embed = discord.Embed(
                title="Light Control Panel",
                description="Control your lights with the buttons below",
                color=discord.Color.blue()
            )
            
            # Create view with buttons
            view = LightControlView()
            
            # Send the embed with buttons
            logger.info("Sending control panel embed")
            await channel.send(embed=embed, view=view)
            logger.info("Control panel sent successfully")
            
            self.setup_complete = True
            
        except Exception as e:
            logger.error(f"Error in setup_control_panel: {e}")

    # Add a manual command to create the panel
    @commands.command(name="setuplight")
    @commands.has_permissions(administrator=True)
    async def setup_light_command(self, ctx):
        await ctx.send("Setting up light control panel...")
        await self.setup_control_panel()
        await ctx.send("Setup complete!")

class LightControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view that doesn't timeout
    
    @discord.ui.button(label="Light ON", style=discord.ButtonStyle.green, custom_id="light_on")
    async def light_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info("Light ON button pressed")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(LIGHT_ON_WEBHOOK) as response:
                    if response.status == 200:
                        await interaction.response.send_message("Light turned ON!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Failed to turn light ON. Status: {response.status}", ephemeral=True)
            except Exception as e:
                logger.error(f"Error in light_on: {e}")
                await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Light OFF", style=discord.ButtonStyle.red, custom_id="light_off")
    async def light_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info("Light OFF button pressed")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(LIGHT_OFF_WEBHOOK) as response:
                    if response.status == 200:
                        await interaction.response.send_message("Light turned OFF!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Failed to turn light OFF. Status: {response.status}", ephemeral=True)
            except Exception as e:
                logger.error(f"Error in light_off: {e}")
                await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot):
    logger.info("Adding LightControl cog to bot")
    await bot.add_cog(LightControl(bot))
    logger.info("LightControl cog added successfully")
