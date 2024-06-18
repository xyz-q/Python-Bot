import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Define intents (adjust based on your bot's needs)
intents = discord.Intents.all()

# Initialize bot with intents
bot = commands.Bot(command_prefix=',', intents=intents)

# Constants (define your constants here)
channel_id = 1233730369937870858
command_log_channel_id = 1233730369937870858
GUILD_ID = '1056994840925192252'
json_folder = '.json'
json_file_path = os.path.join(json_folder, 'mocked_users.json')
AFK_FILE = os.path.join(json_folder, 'afk_users.json')
AUTO_DELETE_FILE = os.path.join(json_folder, 'auto_delete.json')
trusted_role_name = ".trusted"
allowed_channel_name = "admin-commands"
trusted_role_id = 1084779817775411210
allowed_channel_id = 1176833761787265034

# Event: on_ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print("\033[93mBot is now operating\033[0m")
    print("\033[0;33m" + f"Logged in as {bot.user}" + "\033[0m")
    print("\033[0;32mGuilds:\033[0m")

    # Print connected guilds
    for guild in bot.guilds:
        print("\033[36m- {}\033[0m: {}".format("\033[92m" + str(guild.id) + "\033[0m",
                                               "\033[92m" + guild.name + "\033[0m"))

    # Send online message to specified channel
    channel_name = "bot-status"  # Replace with the actual channel name
    channel_type = discord.ChannelType.text  # Adjust the channel type if needed (text, voice, etc.)
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name, type=channel_type)

    if channel:
        try:
            await channel.send(":green_circle: xyz is now online")
            print("\033[90mMessage sent successfully.\033[0m")
        except Exception as e:
            print(f"An error occurred while sending the message: {e}")
    else:
        print("\033[91mChannel not found.\033[0m")

    # Connect to owner's voice channel if present
    owner = bot.get_user(110927272210354176)

    if owner:
        for guild in bot.guilds:
            member = guild.get_member(110927272210354176)

            if member and member.voice:
                voice_channel = member.voice.channel
                await voice_channel.connect()
                break

    # Load cogs after bot is ready
    await load_cogs()

# Function to load all cogs
async def load_cogs():
    for root, _, files in os.walk('./cogs'):
        for file in files:
            if file.endswith('.py'):
                cog_path = os.path.join(root, file)
                # Adjust the module path based on the folder structure
                module = '.'.join(cog_path.split(os.sep))[:-3]
                try:
                    await bot.load_extension(module)
                    print(f'Loaded cog: {module}')
                except Exception as e:
                    print(f'Failed to load cog {module}: {e}')

# Check if a specific cog is loaded
def is_cog_loaded(cog_name):
    return cog_name in bot.cogs

# Command to list all loaded cogs
@bot.command()
async def list_cogs(ctx):
    loaded_cogs = '\n'.join(bot.cogs.keys())
    await ctx.send(f"Loaded cogs:\n```\n{loaded_cogs}\n```")

if __name__ == '__main__':
    # Ensure asyncio event loop is used
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(DISCORD_TOKEN))
