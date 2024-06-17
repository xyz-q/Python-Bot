import discord
from discord import FFmpegPCMAudio
from discord import app_commands
import discord.ext.commands as commands
from dotenv import load_dotenv
import youtube_dl
import asyncio
from discord.ext import commands, tasks
import typing
import os
import sys
import subprocess
import json
from pydub import AudioSegment
from pydub.playback import play
import logging
import re
import traceback
from datetime import datetime
AUDIO_FILE_PATH = 'Uwu Anime - Sound Effects (320).mp3'
import atexit
import random
import aiohttp
import re
import io
from concurrent.futures import ThreadPoolExecutor
import typing




# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Define bot intents
intents = discord.Intents.all()
intents.voice_states = True
intents.message_content = True  # Ensure the bot can read message content


# Create the client and bot instances
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=',', intents=intents)

# Bot setup
channel_id = 1233730369937870858  # Replace with the actual channel ID
channel = bot.get_channel(1233730369937870858)
command_log_channel_id = 1233730369937870858  # Replace with the ID of your command log channel
GUILD_ID = '1056994840925192252'

# Command list
commands_list = [
    ("/setup", "Bot setup info (This is the only /slash command)"),
    (",autodelete", "Toggles the bot's autodelete function"),
    (",avatar <@user>", "Gets user's avatar"),
    (",afk", "Toggle your status of AFK"),
    (",clearq ", " Removes all music from the queue"),
    (",dnd", "Toggles the bot between DnD and Idle Mode"),
    (",disconnect <@user>", "Disconnect user from a voice channel"),
    (",drag <@user>", " Move a user to a voice channel"),
    (",emojiadd <link>", " Creates an emoji"),
    (",emoji ", " Gives details of an emoji"),
    (",emojiremove <name>", " Deletes an emoji"),
    (",deafen <@user>", "Deafens the target user, if none is specified it deafens the bot"),
    (",gather <#channel>", "Moves all users into the voice channel that you are in or the channel specified."),
    (",join <channel-name> (optional)", "Joins the channel you're in, or if specified it joins the channel name"),
    (",jail <@user>", "Assigns the user to the '.jail' role"),
    (",kill ", " KILLS THE BOT [restricted command] "),
    (",kick <@user(s)> {reason}", "Kicks the user(s) from the server"),
    (",leave", "Leaves the channel the bot is in"),
    (",mock <@user>", "Mocks target user(s)"),
    (",mute <@user>", "Mutes target user"),
    (",mp3list ", "Shows a list of mp3s in the file"),
    (",names <@user>", "Gets the old nicknames of a user"),
    (",online ", "Sets bot status as 'Online'"),
    (",offline", "Sets bot status as 'Offline'"),
    (",pause ", " Halts audio playback"),
    (",play <URL/Search>", "Plays youtube music"),
    (",playmp3 <mp3>", "Plays Target MP3"),
    (",ping", "Ping command - Test if the bot is responsive- displays the latency from the bot to the server"),
    (",purge <#channel/number> <number>", "Deletes messages in #channel if specified, default is 100"),
    (",q ", " Shows the music queue"),
    (",release <@user>", "Releases the user from the '.jail' role"),
    (",resetstatus", "Resets the bot's status"),
    (",resume", " Continues audio playback"),
    (",stalk <@user>", "Stalks the specified user"),
    (",stopstalk", "Stops stalking selected user"),
    (",setstatus <activity-type> <status>", "Sets the bot's status"),
    (",senddm <target> <message > ", "Sends a message to target user"),
    (",skip ", " Skips a song in queue"),
    (",say <#channel> 'TEXT'' ", "Makes the bot chat the desired text in specified channel"),
    ("/ticket", "Creates a ticket"),
    (",user <@user>", "Displays info on user"),
    (",volume <1-100>", "Sets the bot's volume"),
    (",viewdms <target>", " Shows the bot's dms with a user"),

# : (", ", " "),

]




# Global variable for pagination
per_page = 5

# Function to send list with pagination
async def send_list(ctx, page, message=None):
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    commands_page = commands_list[start_index:end_index]

    embed = discord.Embed(title=f"Available Commands (Page {page})", color=discord.Color.dark_grey())
    for command, description in commands_page:
        embed.add_field(name=command, value=description, inline=False)

    embed.set_footer(text=f"Page {page}/{(len(commands_list) - 1) // per_page + 1}")

    if message:
        await message.edit(embed=embed)
    else:
        message = await ctx.send(embed=embed)
        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('❌')  # Add delete reaction

    return message

# Command to list commands
@bot.command()
async def list(ctx, page: int = 1):
    # Delete the command invocation message
    await ctx.message.delete()

    # Send the list of commands only to the user who invoked the command as an ephemeral message
    message = await send_list(ctx, page)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️', '❌']  # Check for delete reaction

    try:
        while True:
            reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)

            if str(reaction.emoji) == '⬅️':
                page = max(1, page - 1)
            elif str(reaction.emoji) == '➡️':
                page = min((len(commands_list) - 1) // per_page + 1, page + 1)
            elif str(reaction.emoji) == '❌':  # Delete reaction clicked
                await message.delete()  # Delete the message
                return

            await send_list(ctx, page, message=message)
            await message.remove_reaction(reaction.emoji, user)

    except asyncio.TimeoutError:
        await message.delete()  # Delete the message after timeout

# Handle command errors to prevent the bot from exiting unexpectedly
@bot.event
async def on_command_error(ctx, error):
    try:
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass  # If the message is not found, we pass since it might be already deleted.

    if isinstance(error, commands.CommandNotFound):
        bot_message = await ctx.send(f":warning: Command '{ctx.invoked_with}' not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        bot_message = await ctx.send("Missing required argument.")
    else:
        bot_message = await ctx.send("An error occurred.")
        print(f"An error occurred: {error}")

    await asyncio.sleep(7)
    await bot_message.delete()


# List : End of the list

# Variable to track the bot's current status
is_dnd = True

# Activity to set when the bot is in Do Not Disturb mode
dnd_activity = discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/VGucfdymCm")

# Activity to set when the bot is in Online mode
idle_activity = discord.Activity(type=discord.ActivityType.listening, name="@.zxpq")

# Slash : First Test slash command
@bot.tree.command(name="setup", description="Shows the user how to setup the bot properly.")
async def hello(interaction: discord.Interaction):
    help_message = (
        "To set up the bot with your server, you need to:\n"
        "1. Create a role named `.trusted`\n"
        "2. Create a text channel named `admin-commands`\n"
        "3. Also create a text channel named `tickets`\n\n"
        "After that, you can execute commands in the `admin-commands` channel.\n\n"
        "Note: You must have the role `.trusted` in order to process commands, the command prefix is ','"
    )
    await interaction.response.send_message(help_message, ephemeral=True)
    print("\033[95mUser has used a /slash command.")

# Slash command : ticket command
@bot.tree.command(name="ticket", description="Open a ticket")
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_modal(TicketModal())


# Command : Command to sync bot tree
@bot.command()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Slash commands synchronized successfully!")
    await print("Slash commands synchronized successfully!")

# Command : Disconnect (Disconnect users from channel)
@bot.command()
async def disconnect(ctx, *members: discord.Member):
    if not members:
        await ctx.send("Please mention one or more users to disconnect.")
        return

    disconnected_members = []
    for member in members:
        if not member.voice:
            await ctx.send(f"{member.display_name} is not in a voice channel.")
            continue
        try:
            # Move member to a non-existent voice channel (disconnect them)
            await member.move_to(None)
            disconnected_members.append(member.display_name)
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to disconnect {member.display_name} from their voice channel.")
        except discord.HTTPException:
            await ctx.send(f"An error occurred while trying to disconnect {member.display_name}.")

    if disconnected_members:
        await ctx.send(f"Disconnected {', '.join(disconnected_members)} from their voice channels.")


@bot.command()
async def join(ctx, *, channel_keyword: str = None):
    # Disconnect from the current voice channel, if any
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    if channel_keyword:
        # Check if the keyword matches any voice channel name in the guild
        matched_channels = [channel for channel in ctx.guild.voice_channels if
                            channel_keyword.lower() in channel.name.lower()]

        if not matched_channels:
            await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
            return

        # If multiple channels match, ask the user to specify further
        if len(matched_channels) > 1:
            await ctx.send(f"Multiple voice channels match the keyword '{channel_keyword}'. Please specify further.")
            return

        channel = matched_channels[0]
    else:
        # If no keyword provided, use the channel of the command invoker
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel to use this command.")
            return
        channel = ctx.author.voice.channel

    # Connect to the voice channel
    await channel.connect()
    await ctx.send(f"Joined {channel.name}")




# Command : Gather
@bot.command()
async def gather(ctx, target_channel_keyword: str = None):
    # Check if the command invoker is in a voice channel
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("You need to be in a voice channel to use this command or specify a target channel!")
        return

    # If no target channel keyword is specified, use the invoker's channel
    if target_channel_keyword is None:
        target_channel = ctx.author.voice.channel
    else:
        # Find the target voice channel using the keyword
        matched_channels = [channel for channel in ctx.guild.voice_channels if
                            target_channel_keyword.lower() in channel.name.lower()]

        if not matched_channels:
            await ctx.send(f"No voice channel matching the keyword '{target_channel_keyword}' found.")
            return

        # If multiple channels match, ask the user to specify further
        if len(matched_channels) > 1:
            await ctx.send(
                f"Multiple voice channels match the keyword '{target_channel_keyword}'. Please specify further.")
            return

        target_channel = matched_channels[0]

    # Get all voice channels in the guild
    voice_channels = ctx.guild.voice_channels

    # Iterate over each voice channel
    for channel in voice_channels:
        # Check if the channel is not the target channel
        if channel != target_channel:
            # Iterate over each member in the voice channel
            for member in channel.members:
                # Move the member to the target channel
                await member.move_to(target_channel)

    await ctx.send(f"All members have been gathered to {target_channel.mention}.")


# Command: Drag (example command)
@bot.command()
async def drag(ctx, channel_keyword: str, *members: discord.Member):
    # Find the target voice channel using the keyword
    matched_channels = [channel for channel in ctx.guild.voice_channels if
                        channel_keyword.lower() in channel.name.lower()]

    if not matched_channels:
        await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
        return

    # If multiple channels match, ask the user to specify further
    if len(matched_channels) > 1:
        await ctx.send(f"Multiple voice channels match the keyword '{channel_keyword}'. Please specify further.")
        return

    target_channel = matched_channels[0]

    if not members:
        await ctx.send("Please mention one or more users to drag.")
        return

    moved_members = []
    for member in members:
        if not member.voice:
            await ctx.send(f"{member.display_name} is not in a voice channel.")
            print(f"User  {', '.join(moved_members)} 'is not in a voice channel")
            continue
        try:
            await member.move_to(target_channel)
            moved_members.append(member.display_name)
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to drag {member.display_name} to {target_channel.name}.")
        except discord.HTTPException:
            await ctx.send(f"An error occurred while trying to drag {member.display_name}.")

    if moved_members:
        await ctx.send(f"Dragged {', '.join(moved_members)} to {target_channel.name}")
        print(f"Dragged {', '.join(moved_members)} to {target_channel.name}")


# Command : Stalks user in VC
followed_user = None
@bot.command()
async def stalk(ctx, member: discord.Member):
    global followed_user

    # Check if the bot is already in a voice channel
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        # If the bot is already in a voice channel, don't connect to another one
        voice_channel = voice_client.channel
    else:
        voice_channel = None

    # Connect/move to the voice channel if available
    if member.voice and member.voice.channel:
        voice_channel = member.voice.channel
        try:
            if not voice_client:
                await voice_channel.connect()
            else:
                await voice_client.move_to(voice_channel)
        except discord.ClientException:
            await ctx.send("Failed to connect to the voice channel.")
            return
    else:
        await ctx.send(f" {member.display_name} is not in a voice channel, or the bot isn't in a voice channel. Starting the loop anyway...", delete_after=1)

        print(f"Started stalking {member.display_name} even though they are not in a voice channel.")

    followed_user = member
    await ctx.send(f"Now stalking {member.display_name} in {voice_channel.name}.", delete_after=1)
    print(f"\033[30mNow stalking\033[0m \033[91m{member.display_name}\033[0m \033[30min\033[0m \033[91m{voice_channel.name}\033[0m.")
    await ctx.message.delete(delay=1)

# Command : Stopstalk command
@bot.command()
async def stopstalk(ctx):
    global followed_user

    if followed_user:
        voice_client = ctx.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
        await ctx.send(f"Stopped stalking {followed_user.display_name}.")
        followed_user = None
    else:
        await ctx.send("The bot is not currently stalking anyone.")

# Loop : Stalking loop
@tasks.loop(seconds=4)
async def follow_user():
    global followed_user

    if followed_user and followed_user.voice:
        guild = followed_user.guild
        voice_channels = guild.voice_channels

        # Check if the followed user is still in a voice channel
        if followed_user.voice.channel is None:
            print(f"{followed_user.display_name} has left the voice channel. Stopping the loop.")
            await follow_user.stop()  # Stop the loop if the user has left the voice channel
            return

        # Check all voice channels for the user
        for voice_channel in voice_channels:
            if followed_user in voice_channel.members:
                # User found in this channel, join it
                voice_client = guild.voice_client

                if voice_client is None:
                    try:
                        # Connect to the user's voice channel
                        await voice_channel.connect(timeout=5)
                    except discord.ClientException:
                        pass  # Failed to connect, may already be connected elsewhere or missing permissions
                else:
                    if voice_client.is_connected() and voice_client.channel:
                        # Check if the bot is already in the user's channel
                        if voice_client.channel != voice_channel:
                            try:
                                # Move the bot to the user's voice channel
                                await voice_client.move_to(voice_channel)
                            except (discord.ClientException, AttributeError):
                                pass  # Failed to move, likely due to missing permissions or channel restrictions
                    else:
                        try:
                            # Reconnect to the user's voice channel
                            await voice_client.connect(reconnect=True, timeout=5)
                        except discord.ClientException:
                            pass  # Failed to reconnect, may already be connected elsewhere or missing permissions

                # User found, break out of the loop
                break






# Command : Volume Command
@bot.command()
async def volume(ctx, volume_percent: int):
    # Check if the user is in a voice channel
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel to adjust the volume.")
        return

    # Get the voice client
    voice_client = ctx.voice_client

    # Check if the bot is currently playing audio
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("No audio is currently playing.")
        return

    # Check if the volume is within the valid range (10% - 100%)
    if not 10 <= volume_percent <= 100:
        await ctx.send("Volume must be between 10% and 100%.")
        return

    # Calculate the volume factor
    volume_factor = volume_percent / 100

    # Adjust the volume using FFmpeg options
    volume_option = f"volume={volume_factor}"
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=volume_option)

    await ctx.send(f"Volume set to {volume_percent}%.")



# Command : Deafen The bot
@bot.command()
async def deafen(ctx, target: str = None):
    # If no target is specified, default to the invoking user
    if target is None:
        target = ctx.author
    # If target is "bot", set it to the bot user
    elif target.lower() == "bot":
        target = ctx.guild.me
    else:
        # Attempt to find the member with the given name or mention
        target = discord.utils.get(ctx.guild.members, name=target)
        if target is None:
            await ctx.send("Target not found.")
            return

    # Check if the target user is in a voice channel
    if not target.voice:
        await ctx.send(f"{target.display_name} is not in a voice channel.")
        return

    # Check if the user invoking the command has permission to deafen members
    if not ctx.author.guild_permissions.deafen_members:
        await ctx.send("You do not have permission to deafen members.")
        return

    # Check if the bot has permission to deafen members
    if not ctx.guild.me.guild_permissions.deafen_members:
        await ctx.send("I do not have permission to deafen members.")
        return

    # Toggle the deafen status of the target user
    deafened = not target.voice.deaf
    await target.edit(deafen=deafened)

    # Send a message indicating the deafen status
    if deafened:
        await ctx.send(f"{target.display_name} has been deafened.")
    else:
        await ctx.send(f"{target.display_name} has been undeafened.")



# Error handling for missing permissions
@deafen.error
async def deafen_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("I'm sorry, you do not have permission to do that.")

# Command : Mute command
@bot.command()
async def mute(ctx, target: discord.Member = None):
    # If no target is specified, send an error message
    if target is None:
        await ctx.send("Please specify a user to mute.")
        return

    # Check if the user invoking the command has permission to mute members
    if not ctx.author.guild_permissions.mute_members:
        await ctx.send("You do not have permission to mute members.")
        return

    # Check if the bot has permission to mute members
    if not ctx.guild.me.guild_permissions.mute_members:
        await ctx.send("I do not have permission to mute members.")
        return

    # Toggle the mute status of the target user
    muted = not target.voice.mute
    await target.edit(mute=muted)

    # Send a message indicating the mute status
    if muted:
        await ctx.send(f"{target.display_name} has been muted.")
    else:
        await ctx.send(f"{target.display_name} has been unmuted.")


# Error handling for missing permissions and missing target
@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("I'm sorry, you do not have permission to do that.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify a user to mute.")





# Command: `playmp3`
@bot.command()
async def playmp3(ctx, *keywords: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel to play a sound.")
        return

    voice_channel = ctx.author.voice.channel

    try:
        if ctx.voice_client is None:
            voice_client = await voice_channel.connect()
        else:
            voice_client = ctx.voice_client

        current_dir = os.path.dirname(os.path.abspath(__file__))
        soundboard_dir = os.path.join(current_dir, 'soundboard')

        # Get all mp3 files in the soundboard directory
        mp3_files = [file for file in os.listdir(soundboard_dir) if file.endswith('.mp3')]

        # Find mp3 files that match any of the keywords
        matched_files = []
        for keyword in keywords:
            for mp3_file in mp3_files:
                if keyword.lower() in mp3_file.lower():
                    matched_files.append(mp3_file)

        if not matched_files:
            await ctx.send("No matching mp3 files found.")
            return

        # If multiple matches found, inform the user and let them choose
        if len(matched_files) > 1:
            await ctx.send(f"Multiple matching files found: {', '.join(matched_files)}. Please specify a more specific keyword.")
            return

        mp3_file = os.path.join(soundboard_dir, matched_files[0])

        if not os.path.exists(mp3_file):
            await ctx.send(f"{matched_files[0]} file not found in the soundboard.")
            return

        if not voice_client.is_playing():
            voice_client.play(discord.FFmpegPCMAudio(mp3_file))
            await ctx.send(f"Playing {matched_files[0]}.")
            while voice_client.is_playing():
                await asyncio.sleep(1)
    except Exception as e:
        print(f"Error playing mp3: {e}")
        await ctx.send("An error occurred while trying to play the mp3.")









# Command : Stop mp3
async def stop_audio(ctx):
    if ctx.voice_client is not None and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Audio playback stopped.")
    else:
        await ctx.send("No audio is currently playing.")

# Command to stop audio playback
@bot.command()
async def stop(ctx):
    await stop_audio(ctx)


# Command to list songs in file
@bot.command()
async def mp3list(ctx):
    # Path to the 'soundboard' folder
    soundboard_folder = 'soundboard'

    # Check if the 'soundboard' folder exists
    if not os.path.exists(soundboard_folder):
        await ctx.send("The 'soundboard' folder does not exist.")
        return

    # Get a list of all files in the 'soundboard' folder
    sound_files = [file for file in os.listdir(soundboard_folder) if file.endswith('.mp3')]

    # Check if there are no .mp3 files in the 'soundboard' folder
    if not sound_files:
        await ctx.send("No .mp3 files found in the 'soundboard' folder.")
        return

    # Send the list of .mp3 files
    await ctx.send("List of available songs:")
    for song in sound_files:
        await ctx.send(song)



# Suppress noise about console usage from youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Global variables for queue and voice client

is_playing = False  # Initialize is_playing as False initially
voice_client = None
queue = []
current_playing_url = None
loop_song = False
executor = ThreadPoolExecutor()


# ytdl options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Command to play audio from YouTube link
@bot.command()
async def YOUTUBE(ctx, *, query):
    author = ctx.message.author
    voice_channel = author.voice.channel if author.voice else None

    if not voice_channel:
        await ctx.send('You need to be in a voice channel to use this command.')
        return

    voice_client = ctx.guild.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(voice_channel)
    else:
        voice_client = await voice_channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,  # Prevent downloading playlists
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch:{query}', download=False)
        except youtube_dl.DownloadError as e:
            await ctx.send(f'Error downloading video: {e}')
            return
        except youtube_dl.ExtractorError as e:
            await ctx.send(f'Error extracting info: {e}')
            return

        if 'entries' in info:
            # Use the first video in the search results
            video = info['entries'][0]
            url = video['url']
            title = video['title']
            await ctx.send(f'Now playing: {title}')
            voice_client.play(discord.FFmpegPCMAudio(url))
        else:
            await ctx.send(f'No video found for query: {query}')


@bot.command()
async def play(ctx, *, query):
    global queue, current_playing_url

    author = ctx.message.author
    voice_channel = author.voice.channel if author.voice else None

    if not voice_channel:
        await ctx.send('You need to be in a voice channel to use this command.')
        return

    voice_client = ctx.guild.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(voice_channel)
    else:
        voice_client = await voice_channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,  # Prevent downloading playlists
    }

    info = await download_info(query, ydl_opts)
    if info is None:
        await ctx.send(f'No video found for query: {query}')
        return

    if 'entries' in info:
        video = info['entries'][0]
        url = video['url']
        title = video['title']

        download_msg = await ctx.send(f'Downloading: {title}')
        await asyncio.sleep(4)  # Simulate downloading delay


        if voice_client.is_playing():
            queue.append(query)
            await ctx.send(f'Added to queue: {title}')
            await download_msg.delete()  # Delete download message if added to queue
        else:
            await download_msg.delete()  # Delete download message if starting to play now
            await ctx.send(f'Now playing: {title}')
            current_playing_url = url
            voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    else:
        await ctx.send(f'No video found for query: {query}')

async def download_info(query, ydl_opts):
    loop = asyncio.get_event_loop()
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = await loop.run_in_executor(executor, lambda: ydl.extract_info(f'ytsearch:{query}', download=False))
            return info
        except youtube_dl.DownloadError as e:
            print(f'Error downloading video: {e}')
            return None
        except youtube_dl.ExtractorError as e:
            print(f'Error extracting info: {e}')
            return None

async def play_next(ctx):
    global queue, current_playing_url

    if queue:
        next_query = queue.pop(0)
        author = ctx.message.author
        voice_channel = author.voice.channel if author.voice else None

        if not voice_channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            return

        voice_client = ctx.guild.voice_client

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,  # Prevent downloading playlists
        }

        info = await download_info(next_query, ydl_opts)
        if info is None:
            await ctx.send(f'No video found for query: {next_query}')
            return

        if 'entries' in info:
            video = info['entries'][0]
            url = video['url']
            title = video['title']
            await ctx.send(f'Now playing: {title}')
            current_playing_url = url
            voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

@bot.command()
async def q(ctx):
    if not queue:
        await ctx.send('The queue is currently empty.')
    else:
        queue_list = '\n'.join([f'{index + 1}. {item}' for index, item in enumerate(queue)])
        await ctx.send(f'**Current Queue:**\n{queue_list}')

@bot.command()
async def clearq(ctx):
    global queue
    if not queue:
        await ctx.send('The queue is already empty.')
    else:
        queue.clear()
        await ctx.send('Queue cleared.')



@bot.command()
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send('Playback paused.')
    else:
        await ctx.send("I'm not playing anything right now.")

@bot.command()
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send('Playback resumed.')
    else:
        await ctx.send("I'm not paused right now.")



@bot.command()
async def skip(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send('Skipped the current song.')
        await play_next(ctx)
    else:
        await ctx.send("I'm not playing anything right now.")


@bot.command()
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        await voice_client.disconnect()
        queue.clear()
    else:
        await ctx.send("I'm not connected to any voice channel.")


# Command to reset status to default
@bot.command()
async def resetstatus(ctx):
    await bot.change_presence(activity=default_status)
    await ctx.send("Status reset to default.")

# Command to toggle bot status between "Do Not Disturb" and "Idle"
@bot.command()
async def dnd(ctx):
    global is_dnd
    is_dnd = not is_dnd  # Toggle the status

    if is_dnd:
        await bot.change_presence(status=discord.Status.dnd, activity=dnd_activity)
        await ctx.send("Bot status set to Do Not Disturb.")
        print("\033[91mBot is now in Do Not Disturb mode.\033[0m")
    else:
        await bot.change_presence(status=discord.Status.idle, activity=idle_activity)
        await ctx.send("Bot status set to Idle.")
        print("\033[33mBot is now in Idle mode.\033[0m")

# Command : Online command
@bot.command()
async def online(ctx):

    # Set the bot's status to online
    await bot.change_presence(status=discord.Status.online)
    await ctx.send("Bot status set to Online.")
    print("\033[92mBot is now in Online mode.\033[0m")

# Command : Offline command
@bot.command()
async def offline(ctx):
    await bot.change_presence(status=discord.Status.offline)
    await ctx.send("Bot is now appearing offline.")
    print("Bot is now appearing offline")


# Command to set custom status
@bot.command()
async def setstatus(ctx, activity_type: str, *, status: str):
    activity_type = activity_type.lower()
    if activity_type not in ["playing", "listening", "watching", "streaming"]:
        await ctx.send("Invalid activity type. Please choose from: playing, listening, watching, streaming.")
        return

    if not status:
        await ctx.send("Please provide a <status>.")
        return

    activity_type_enum = discord.ActivityType.playing
    if activity_type == "listening":
        activity_type_enum = discord.ActivityType.listening
    elif activity_type == "watching":
        activity_type_enum = discord.ActivityType.watching
    elif activity_type == "streaming":
        activity_type_enum = discord.ActivityType.streaming

    await bot.change_presence(activity=discord.Activity(type=activity_type_enum, name=status))
    await ctx.send(f"Status changed to '[{activity_type.capitalize()}] [{status}]'")

# Default status
default_status = discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/jJ8QcTB3")

# Command to kick members
@bot.command()
async def kick(ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
    # Check if the bot has permission to kick members
    if not ctx.guild.me.guild_permissions.kick_members:
        await ctx.send("I don't have permission to kick members.")
        return

    # Kick each member
    for member in members:
        try:
            await member.kick(reason=reason)
            if reason:
                await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
            else:
                await ctx.send(f"{member.mention} has been kicked.")
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to kick {member.mention}.")
        except discord.HTTPException:
            await ctx.send(f"An error occurred while trying to kick {member.mention}.")

# Command: Ping (test command)
@bot.command()
async def ping(ctx):
    # Get the bot's latency to the server
    bot_latency = round(bot.latency * 1000)  # Latency in milliseconds

    # Create an embed
    embed = discord.Embed(title=" ", description=f"Pong! 🏓\nBot latency: {bot_latency} ms", color=discord.Color.blurple())

    # Send the embed
    await ctx.send(embed=embed)

# Load mocked users data
try:
    with open('mocked_users.json', 'r') as file:
        mocked_users = json.load(file)
except FileNotFoundError:
    mocked_users = {}

# Function to mock a message
async def mock_message(message):
    if message.content.startswith(','):  # Skip mocking if the message contains the command invocation
        return False

    user_id = str(message.author.id)
    if user_id in mocked_users and mocked_users[user_id]:
        mocked_text = ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content))
        await message.channel.send(mocked_text)
        return True
    return False

# Command: Mock command
@bot.command()
async def mock(ctx, target: discord.Member = None):
    if target is None:
        await ctx.send("Please mention a user to toggle mocking.")
        return

    if target.bot and target.name == "xyz":
        await ctx.send("Cannot toggle mocking for bot.")
        return

    # Toggle mocking for the specified user
    user_id = str(target.id)
    mocked_users[user_id] = not mocked_users.get(user_id, False)
    with open('mocked_users.json', 'w') as file:
        json.dump(mocked_users, file)
    if mocked_users[user_id]:
        await ctx.send(f"Mocking enabled for {target.display_name}.")
    else:
        await ctx.send(f"Mocking disabled for {target.display_name}.")


# Command : Say command
@bot.command()
async def say(ctx, channel: discord.TextChannel, *, message):
    # Print the user who sent the text and the text itself in purple
    print(f"\033[95mUser: {ctx.author.name} ({ctx.author.id}) said: {message}\033[0m")

    # Send the message to the specified channel
    await channel.send(message)

# Command : Purge command to delete specified messages in specified channel
@bot.command()
async def purge(ctx, channel: typing.Optional[discord.TextChannel] = None, limit: int = 100):
    if limit <= 0:
        await ctx.send("Please specify a positive number for the limit.")
        return

    if limit > 300:
        await ctx.send("Limit cannot exceed 300.")
        return

    if channel is None:
        channel = ctx.channel

    try:
        # Define a check function to delete all messages in the channel
        def check(message):
            return True

        # Attempt to delete messages in batches of 5 until the limit is reached
        total_deleted = 0
        while total_deleted < limit:
            to_delete = min(limit - total_deleted, 5)
            deleted = await channel.purge(limit=to_delete, check=check)
            total_deleted += len(deleted)

            # Add a short delay between batches to prevent rate limits
            await asyncio.sleep(1)

        # Send the final result after completion
        confirmation_msg = await ctx.send(f"Purged {total_deleted} message(s) from {channel.mention}.")
        await asyncio.sleep(5)
        await confirmation_msg.delete()

    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while purging messages: {e}")



# Modal: ticket modal
class TicketModal(discord.ui.Modal, title="Ticket Submission"):
    subject = discord.ui.TextInput(label="Subject", style=discord.TextStyle.short, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        subject = self.subject.value
        description = self.description.value

        # Ensure guild exists before accessing its attributes
        if interaction.guild:
            # Check if interaction occurs in a DM channel
            if isinstance(interaction.channel, discord.DMChannel):
                await interaction.response.send_message("Slash commands are not available in DMs.", ephemeral=True)
                return

            # Assuming 'tickets' channel exists
            ticket_channel = discord.utils.get(interaction.guild.text_channels, name="tickets")

            if ticket_channel is not None:
                embed = discord.Embed(title="New Ticket", color=discord.Color.dark_grey())
                embed.add_field(name="Subject", value=subject, inline=False)
                embed.add_field(name="Description", value=description, inline=False)
                embed.add_field(name="Submitted by", value=interaction.user.name, inline=False)  # Changed to use username

                view = TicketButtons(interaction.user, subject, description)

                await ticket_channel.send(embed=embed, view=view)
                await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True)
            else:
                await interaction.response.send_message("Ticket channel not found. Please contact an administrator.",
                                                        ephemeral=True)
        else:
            await interaction.response.send_message("Tickets have to be sent in a guild, silly! :3 /setup for more info", ephemeral=True)


class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user: discord.User, subject: str, description: str):
        super().__init__(timeout=None)
        self.ticket_user = ticket_user
        self.subject = subject
        self.description = description

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.ticket_user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        support_role = discord.utils.get(guild.roles, name=".trusted")  # Adjust role name as needed
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True)

        # Create a new category for the ticket at the bottom
        category = await guild.create_category(
            name=f"Ticket-{self.ticket_user.name}",
            overwrites=overwrites,
            reason="New ticket accepted"
        )
        await category.edit(position=len(guild.categories))  # Move category to the bottom

        # Create the ticket channel within the new category
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{self.ticket_user.name}",
            topic=f"Support ticket for {self.ticket_user.name}",
            reason="New ticket accepted"
        )

        embed = discord.Embed(title="Ticket Details", color=discord.Color.dark_grey())
        embed.add_field(name="Subject", value=self.subject, inline=False)
        embed.add_field(name="Description", value=self.description, inline=False)
        embed.add_field(name="Submitted by", value=self.ticket_user.name, inline=False)

        close_view = CloseTicketButton(self.ticket_user)  # Pass the ticket_user argument here

        await ticket_channel.send(content=f"Hello {self.ticket_user.mention}, a support member will be with you shortly.",
                                  embed=embed, view=close_view)
        await interaction.response.send_message(f"Ticket accepted and channel created: {ticket_channel.mention}",
                                                ephemeral=True)
        await interaction.message.delete()
        await self.ticket_user.send(f"Ticket accepted {ticket_channel.mention} by {interaction.user.name}.")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            # Send rejection message to the user
            await self.ticket_user.send(f"Your ticket has been rejected by {interaction.user.name}.")
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You do not have permission to reject this ticket.", ephemeral=True)


class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_user: discord.User):
        super().__init__(timeout=None)
        self.ticket_user = ticket_user

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            # Send closing message to the user
            await self.ticket_user.send(f"Your ticket has been closed by {interaction.user.name}.")

            # Delete the ticket channel
            await interaction.channel.delete(reason="Ticket closed by support staff")

            # Check if the category is now empty and delete it if so
            category = interaction.channel.category
            if category and len(category.channels) == 0:
                await category.delete(reason="Category empty after ticket closed")
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)










# Define a global dictionary to store previous roles of users
previous_roles = {}

# Command : Jail
@bot.command()
async def jail(ctx, member: discord.Member):
    global previous_roles

    # Check if the role exists
    jail_role = discord.utils.get(ctx.guild.roles, name=".jail")

    if not jail_role:
        await ctx.send("The .jail role does not exist.")
        return

    # Store the user's current roles
    previous_roles[member.id] = [role.id for role in member.roles]

    # Remove all other roles
    await member.edit(roles=[jail_role])

    # Toggle the .jail role
    if jail_role in member.roles:
        await ctx.send(f"{member.display_name} has been banished.")
    else:
        await ctx.send(f"Failed to banish {member.display_name}.")

# Command : Release the user
@bot.command()
async def release(ctx, member: discord.Member):
    global previous_roles

    # Check if the role exists
    jail_role = discord.utils.get(ctx.guild.roles, name=".jail")

    if not jail_role:
        await ctx.send("The .jail role does not exist.")
        return

    # Remove the .jail role
    await member.remove_roles(jail_role)

    # Restore the user's previous roles
    roles_to_add = [ctx.guild.get_role(role_id) for role_id in previous_roles.get(member.id, [])]
    if roles_to_add:
        await member.edit(roles=roles_to_add)
        await ctx.send(f"{member.display_name} has been released from jail. Their previous roles have been restored.")
    else:
        await ctx.send("Failed to restore previous roles.")

# Command to add or remove roles
@bot.command()
async def role(ctx, *, args: str):
    # Check if the bot has permission to manage roles
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("I don't have permission to manage roles.")
        return

    # Check if the caller has permission to manage roles
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You don't have permission to manage roles.")
        return

    # Parse the arguments
    args = args.split()
    if len(args) != 2:
        await ctx.send("Please provide both a member and a role.")
        return

    member_str, role_str = args
    member = discord.utils.get(ctx.guild.members, mention=member_str)

    # Extract role from mention
    if role_str.startswith("<@&") and role_str.endswith(">"):
        role_id = role_str[3:-1]
        role = discord.utils.get(ctx.guild.roles, id=int(role_id))
    else:
        role = discord.utils.get(ctx.guild.roles, name=role_str)

    # Check if a member and role are provided
    if member is None or role is None:
        await ctx.send("Invalid member or role provided.")
        return

    # Check if the bot can manage the role
    if ctx.guild.me.top_role <= role:
        await ctx.send("I can't manage roles higher than my top role.")
        return

    # Check if the user can manage the role
    if ctx.author.top_role <= role:
        await ctx.send("You can't manage roles higher than your top role.")
        return

    # Check if the member already has the role
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Removed the {role.name} role from {member.mention}.")
    else:
        await member.add_roles(role)
        await ctx.send(f"Added the {role.name} role to {member.mention}.")



# Command: Hello (example command)
@bot.command()
async def hello(ctx):
    await ctx.send("Hello world!")

# Event : Welcome message  and ticket
# Channel ID where the ticket message will be sent
TICKET_CHANNEL_ID = 1241495094205354104  # Replace with your tickets channel ID
# Channel name for welcome messages
WELCOME_CHANNEL_NAME = "welcome"  # Replace with your welcome channel name
# Role ID to assign when a user is accepted
ROLE_ID = 1056996133081186395  # Replace with the role ID you want to assign
# Replace with your actual guild (server) ID
GUILD_ID = 1056994840925192252

# Dictionary to keep track of active tickets
active_tickets = {}


class AcceptDeclineView(discord.ui.View):
    def __init__(self, user: discord.Member, guild: discord.Guild, message: discord.Message):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.message = message

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = self.guild.get_role(ROLE_ID)
        if role and self.user:
            await self.user.add_roles(role)
            await self.user.send("Welcome to the server! Enjoy your stay.")
        try:
            await self.message.delete()  # Delete the original message
        except discord.errors.NotFound:
            pass  # The message was already deleted

        active_tickets.pop(self.user.id, None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.user.kick(reason="Declined membership.")
        await self.user.send("Access to the server has been declined by an Admin.")
        try:
            await self.message.delete()  # Delete the original message
        except discord.errors.NotFound:
            pass  # The message was already deleted

        active_tickets.pop(self.user.id, None)


class OkayView(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary)
    async def okay(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await self.message.delete()  # Delete the notification message
        except discord.errors.NotFound:
            pass  # The message was already deleted



async def send_ticket_message(member: discord.Member, guild: discord.Guild):
    me2 = await bot.fetch_user(110927272210354176)  # Replace with your Discord user ID
    ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
    if ticket_channel:
        embed = discord.Embed(
            title="New Member Request",
            description=f"{member.mention} has joined the server. Would you like to accept or decline their request?",
            color=discord.Color.gold()
        )
        message = await ticket_channel.send(embed=embed)
        view = AcceptDeclineView(member, guild, message)
        await message.edit(view=view)

        # Track the ticket
        active_tickets[member.id] = message

        # Send notification message to yourself
        await me2.send(f"New User Join {ticket_channel.mention}.")
    else:
        print("Error: Could not find the specified channel for ticket messages.")


async def send_welcome_message(member: discord.Member):
    # Fetch the welcome channel
    channel = discord.utils.get(member.guild.channels, name=WELCOME_CHANNEL_NAME, type=discord.ChannelType.text)

    if channel:
        # Create an embed for the welcome message
        embed = discord.Embed(
            title=f"{member.display_name} pulled up",
            description=f"Username: {member.name}",
            color=discord.Color.red()
        )

        # Fetch avatar URL
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text=f"User ID: {member.id}")

        # Send the welcome message
        await channel.send(embed=embed)
    else:
        print("Error: Could not find the specified channel for welcome messages.")


@bot.event
async def on_member_join(member: discord.Member):
    # Check if the member's guild is the specified guild
    if member.guild.id == GUILD_ID:
        await send_welcome_message(member)
        await send_ticket_message(member, member.guild)


@bot.event
async def on_member_remove(member: discord.Member):
    # Check if the member's guild is the specified guild
    if member.guild.id == GUILD_ID:
        # Remove the active ticket if exists
        if member.id in active_tickets:
            ticket_message = active_tickets.pop(member.id)
            try:
                await ticket_message.delete()
            except discord.errors.NotFound:
                pass

            # Notify the admin
            me2 = await bot.fetch_user(110927272210354176)  # Replace with your Discord user ID
            await me2.send(f"The ticket for {member.mention} has been canceled as they have left/been kicked from the server.")

            # Send a message with "Okay" button to the tickets channel
            ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
            if ticket_channel:
                embed = discord.Embed(
                    title="Ticket Canceled",
                    description=f"The ticket for {member.mention} has been canceled as they have left/been kicked from the server.",
                    color=discord.Color.red()
                )
                cancel_message = await ticket_channel.send(embed=embed)
                okay_view = OkayView(cancel_message)
                await cancel_message.edit(view=okay_view)
        else:
            print("Error: Could not find the specified channel for ticket messages.")

        # Find the channel to send the farewell message
        channel = discord.utils.get(member.guild.channels, name="exit", type=discord.ChannelType.text)

        if channel:
            # Create an embed for the farewell message
            embed = discord.Embed(
                title=f"Goodbye, {member.display_name}!",
                description="We'll miss you.",
                color=discord.Color.dark_grey()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")

            # Send the farewell message
            await channel.send(embed=embed)
        else:
            print("Error: Could not find the specified channel for farewell messages.")

# Ticket : vc ticket
class AcceptDeclineView2(discord.ui.View):
    def __init__(self, member: discord.Member, guild: discord.Guild, message: discord.Message):
        super().__init__(timeout=None)
        self.member = member
        self.guild = guild
        self.message = message

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Move member to the main voice channel
        waiting_room = discord.utils.get(self.guild.voice_channels, name=".waiting-room")
        main_channel = discord.utils.get(self.guild.voice_channels, name=",main")

        if waiting_room and main_channel:
            if self.member.voice and self.member.voice.channel == waiting_room:
                await self.member.move_to(main_channel)

        try:
            await self.message.delete()  # Delete the original message
        except discord.errors.NotFound:
            pass  # The message was already deleted

        active_tickets.pop(self.member.id, None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Kick member from the waiting-room voice channel
        waiting_room = discord.utils.get(self.guild.voice_channels, name=".waiting-room")

        if waiting_room:
            if self.member.voice and self.member.voice.channel == waiting_room:
                await self.member.move_to(None)  # This kicks the member from the voice channel

        try:
            await self.message.delete()  # Delete the original message
        except discord.errors.NotFound:
            pass  # The message was already deleted

        active_tickets.pop(self.member.id, None)

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        if before.channel != after.channel:
            if after.channel is not None:
                print(f"The bot has joined voice channel: {after.channel.name}")
                await asyncio.sleep(2)

                current_dir = os.path.dirname(os.path.abspath(__file__))
                mp3_file = os.path.join(current_dir, 'soundboard', 'uwu.mp3')

                if not os.path.exists(mp3_file):
                    print("uwu.mp3 file not found.")
                    return

                try:
                    if not bot.voice_clients:
                        voice_client = await after.channel.connect()
                    else:
                        voice_client = bot.voice_clients[0]

                    if not voice_client.is_playing():
                        voice_client.play(discord.FFmpegPCMAudio(mp3_file))
                        while voice_client.is_playing():
                            await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error playing mp3: {e}")
    # Replace USER_ID_TO_IGNORE with the ID of the user you want to ignore
    if member.bot or member == bot.user or member.id == 110927272210354176:
        return  # Ignore events triggered by the bot itself, other bots, or the specified user

    # Check if the member joined the .waiting-room voice channel
    if after.channel and after.channel.name == '.waiting-room':
        # Automatically send the voice request message
        await send_voice_request_message(member, member.guild)
    # Check if the member left the .waiting-room voice channel
    elif before.channel and before.channel.name == '.waiting-room' and (not after.channel or after.channel.name != '.waiting-room'):
        # Cancel the ticket if the user left the channel
        await cancel_voice_request(member, member.guild)



# Dictionary to track active tickets
active_tickets = {}


async def send_voice_request_message(member: discord.Member, guild: discord.Guild):
    me = await bot.fetch_user(110927272210354176)  # Replace YOUR_USER_ID with your Discord user ID
    ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
    if ticket_channel:
        embed = discord.Embed(
            title=".waiting-room",
            description=f"{member.mention} has joined the waiting room. Drag them to ,main?",
            color=discord.Color.gold()
        )
        message = await ticket_channel.send(embed=embed)
        view = AcceptDeclineView2(member, guild, message)
        await message.edit(view=view)

        # Store the active ticket
        active_tickets[member.id] = message

        # Send notification message to yourself
        await me.send(f"A user has joined the waiting room {ticket_channel.mention}.")
    else:
        print("Error: Could not find the specified channel for ticket messages.")


class OkayView2(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary)
    async def okay(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.message.delete()

async def cancel_voice_request(member: discord.Member, guild: discord.Guild):
    if member.id in active_tickets:
        message = active_tickets.pop(member.id)
        ticket_channel = bot.get_channel(TICKET_CHANNEL_ID)
        if ticket_channel:
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass  # Message was already deleted or doesn't exist

            embed = discord.Embed(
                title="Ticket Canceled",
                description=f"The ticket for {member.mention} has been dealt with/canceled.",
                color=discord.Color.red()
            )
            cancel_message = await ticket_channel.send(embed=embed)
            view = OkayView2(cancel_message)
            await cancel_message.edit(view=view)




# Command : Shows past nicknames
@bot.command()
async def names(ctx, member: discord.Member):
    # Get the audit logs for the guild
    async for entry in ctx.guild.audit_logs(limit=None, action=discord.AuditLogAction.member_update):
        # Check if the entry is for the specified member
        if entry.target == member:
            # Get the old nickname from the audit log
            old_nick = entry.before.nick
            if old_nick:
                await ctx.send(f"Old nickname for {member.display_name}: {old_nick}")
            else:
                await ctx.send(f"{member.display_name} has not changed their nickname.")
            return
    await ctx.send(f"No nickname change found for {member.display_name}.")

# Command : Shows user info
@bot.command()
async def user(ctx, member: discord.Member = None, user_id: int = None):
    if user_id:
        try:
            member = await ctx.guild.fetch_member(user_id)
        except discord.NotFound:
            await ctx.send("User not found.")
            return
    else:
        member = member or ctx.author

    embed = discord.Embed(title=f"User Info - {member.display_name}", color=member.color)

    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    else:
        default_avatar_url = member.default_avatar.url
        embed.set_thumbnail(url=default_avatar_url)

    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Nickname", value=member.display_name, inline=False)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%a, %d %B %Y, %I:%M %p UTC"), inline=False)
    embed.add_field(name="Join Date", value=member.joined_at.strftime("%a, %d %B %Y, %I:%M %p UTC"), inline=False)

    if member.activity is not None:
        embed.add_field(name="Activity", value=member.activity.name, inline=False)

    boosting_role = discord.utils.get(member.roles, name="Server Booster")
    if boosting_role is not None:
        boosting_status = "Yes"
    else:
        boosting_status = "No"
    embed.add_field(name="Boosting this Server", value=boosting_status, inline=True)

    top_role = member.top_role.name
    embed.add_field(name="Top Role", value=top_role, inline=False)

    await ctx.send(embed=embed)

# Command : Gets users avatar
@bot.command()
async def avatar(ctx, user: discord.User = None, user_id: int = None):
    if user_id:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            await ctx.send("User not found.")
            return
    else:
        user = user or ctx.author

    if user.avatar:
        avatar_url = user.avatar.url
    else:
        avatar_url = user.default_avatar.url

    embed = discord.Embed(title=f"{user.name}'s Avatar", color=ctx.author.color)
    embed.set_image(url=avatar_url)

    await ctx.send(embed=embed)


AFK_FILE = 'afk_users.json'


# Load AFK data from a JSON file
def load_afk_data():
    if os.path.exists(AFK_FILE):
        with open(AFK_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}


# Save AFK data to a JSON file
def save_afk_data(data):
    with open(AFK_FILE, 'w') as file:
        json.dump(data, file, indent=4)


afk_users = load_afk_data()


@bot.command()
async def afk(ctx, *, reason=""):
    user_id = str(ctx.author.id)

    if user_id in afk_users:
        # Remove AFK status
        afk_users.pop(user_id)
        save_afk_data(afk_users)
        await ctx.send(f"{ctx.author.mention} is no longer AFK.")
    else:
        # Set AFK status
        afk_users[user_id] = reason
        save_afk_data(afk_users)
        await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {reason}")


# Event : On ready startup sequence events
@bot.event
async def on_ready():
    bot.load_extension('musiccog')  # Ensure 'musiccog.py' is in the same directory
    follow_user.start()
    global is_dnd
    if is_dnd:
        await bot.change_presence(status=discord.Status.dnd, activity=dnd_activity)
        print("\033[93mBot is now operating\033[0m")
        print("\033[91mBot is now in Do Not Disturb mode.\033[0m")
        print("\033[0;33m" + f"Logged in as {bot.user}" + "\033[0m")
        print("\033[0;32mGuilds:\033[0m")
        for guild in bot.guilds:
            print("\033[36m- {}\033[0m: {}".format("\033[92m" + str(guild.id) + "\033[0m", "\033[92m" + guild.name + "\033[0m"))
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

    # Join channel automatically?

    owner = bot.get_user(110927272210354176)
    if owner:
        for guild in bot.guilds:
            member = guild.get_member(110927272210354176)
            if member and member.voice:
                voice_channel = member.voice.channel
                await voice_channel.connect()
                break

trusted_role_name = ".trusted"
allowed_channel_name = "admin-commands"
trusted_role_id = 1084779817775411210  # Replace this with the ID of your trusted role
allowed_channel_id = 1176833761787265034  # Replace this with your allowed channel ID

# Event: When the bot gets disconnected by Discord's servers
async def on_disconnect():
    # Get the "bot-status" text channel from the guild
    guild = bot.get_guild(1056994840925192252)  # Replace YOUR_GUILD_ID with your guild's ID
    channel = discord.utils.get(guild.text_channels, name="bot-status")

    if channel:
        # Check the bot's connection status
        if bot.is_ready():
            await channel.send(":orange_circle: xyz is experiencing network issues. The bot is still running, but there may be delays in responses.")
        else:
            await channel.send(":red_circle: xyz has been disconnected from Discord's servers. The bot is currently offline.")

# Event: Handling errors during the bot's execution
@bot.event
async def on_error(event, *args, **kwargs):
    # Get the "bot-status" text channel from the guild
    guild = bot.get_guild(1056994840925192252)  # Replace YOUR_GUILD_ID with your guild's ID
    channel = discord.utils.get(guild.text_channels, name="bot-status")

    if channel:

        # Attempt to reconnect the bot
        await channel.send(":orange_circle: Network interruption, attempting to reconnect...")

        # Send the error details as a plain text message
        error_details = f"An error occurred during the `{event}` event.\n" \
                        f"Error details:\n```{traceback.format_exc()}```"
        await channel.send(error_details)
        await bot.close()
        await asyncio.sleep(5)  # Wait for 5 seconds before reconnecting
        await bot.run(DISCORD_TOKEN)

    # You can also perform any other cleanup or logging tasks here

# KILL COMMAND
@bot.command()
async def kill(ctx):
    # Check if the user invoking the command is the specified user
    if ctx.author.id == 110927272210354176:  # Replace with the user ID of .zxpq
        warning_message = await ctx.send(":warning: Are you sure you want to TERMINATE the bot? This action cannot be undone.")
        await warning_message.add_reaction("🔴")  # Red button
        await warning_message.add_reaction("🟢")  # Green button

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["🔴", "🟢"]

        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=10, check=check)
            if str(reaction.emoji) == "🔴":
                await warning_message.clear_reactions()  # Remove reactions
                await warning_message.edit(content=" :orange_circle: Bot TERMINATION cancelled.")
            elif str(reaction.emoji) == "🟢":
                await warning_message.clear_reactions()  # Remove reactions
                await warning_message.edit(content=":warning: Bot instance(s) TERMINATED.")
                print("\033[96m" + f"BOT HAS BEEN TERMINATED BY: {ctx.author.name} ({ctx.author.id})" + "\033[0m")
                guild = bot.get_guild(1056994840925192252)  # Replace YOUR_GUILD_ID with your guild's ID
                channel = discord.utils.get(guild.text_channels, name="bot-status")

                if channel:
                    # Send a message to the "bot-status" text channel indicating that the bot is going offline
                    await channel.send(":red_circle: xyz is now offline [Killed]")
                await bot.close()
        except asyncio.TimeoutError:
            await warning_message.edit(content=":clock1:  Bot TERMINATION cancelled due to inactivity.")
            await warning_message.clear_reactions()  # Remove reactions
    else:
        await ctx.send(f":warning: [ERROR] {ctx.author.mention} is not permitted to operate this command.")
        print("\033[96m" + f"USER TRYING TO KILL BOT: {ctx.author.name} ({ctx.author.id})" + "\033[0m")

# Event : Auto deletion
# File to store the toggle status
AUTO_DELETE_FILE = "auto_delete.json"
ORIGINAL_NAME = "xyz"

# Load auto-delete status from file
try:
    with open(AUTO_DELETE_FILE, "r") as f:
        auto_delete_enabled = json.load(f)
except FileNotFoundError:
    auto_delete_enabled = False

# Command : Auto delete command
@bot.command()
async def autodelete(ctx):
    global auto_delete_enabled
    auto_delete_enabled = not auto_delete_enabled
    await ctx.send(f"Auto-delete commands {'enabled' if auto_delete_enabled else 'disabled'}.")

    # Save auto-delete status to file
    with open(AUTO_DELETE_FILE, "w") as f:
        json.dump(auto_delete_enabled, f)

# Define on_command event
@bot.event
async def on_command(ctx):
    global auto_delete_enabled

    # Check if auto-delete is enabled
    if auto_delete_enabled:
        try:
            # Delete the command message
            await ctx.message.delete()

            # Execute the command and get the bot's response
            bot_response = await ctx.send(ctx.message.content)

            # Delay for 1/2 second
            await asyncio.sleep(0.5)

            # Get bot's messages sent after the command
            async for message in ctx.channel.history(after=ctx.message.created_at):
                if message.author == bot.user:
                    await message.delete()
                else:
                    break  # Exit loop if a non-bot message is encountered
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

    # Update bot's username
    await update_bot_username(ctx)

async def update_bot_username(ctx):
    global auto_delete_enabled

    # Change bot's nickname based on auto-delete setting
    new_nickname = f" 🗑️ {ORIGINAL_NAME} ️" if auto_delete_enabled else ORIGINAL_NAME

    try:
        for guild in bot.guilds:
            await guild.me.edit(nick=new_nickname)
    except discord.HTTPException as e:
        print(f"Failed to update bot's nickname: {e}")


# Event on_message event 

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore messages sent by the bot itself

    if isinstance(message.channel, discord.DMChannel):
        # Respond to DMs with a simple message
        await message.channel.send("hi there :D i can only process commands in a guild. /setup for more info")
        return  # Stop further processing for DMs

    # Check if user is typing in the status channel
    if message.channel.id == 1234310879072223292 and not message.author.bot:
        await message.delete()
        warning_msg = await message.channel.send(f'{message.author.mention}, sending messages in this channel is not allowed.')
        await asyncio.sleep(4)
        await warning_msg.delete()
        return  # Stop further processing for status channel messages

    # Check if the mentioned user(s) are AFK
    mentioned_afk_users = [user_id for user_id in afk_users if message.guild.get_member(int(user_id)) in message.mentions]
    if mentioned_afk_users:
        for user_id in mentioned_afk_users:
            reason = afk_users[user_id]
            user = message.guild.get_member(int(user_id))
            await message.channel.send(f"{user.mention} is currently AFK. Reason: {reason}")

    # Check if the message is a command
    if message.content.startswith(bot.command_prefix):
        # Check if the message is not the setup command
        if not message.content.startswith(bot.command_prefix + "list"):
            # Check if the message is not from the allowed channel
            if message.channel.name != "admin-commands":
                error_message = ":warning: Commands can only be used in the #admin-commands channel. [/setup]"
                response = await message.channel.send(error_message)
                print(f"\033[95m{message.author} Tried to activate command in another channel\033[0m")
                await message.delete()  # Delete the invoker's message instantly
                await asyncio.sleep(4)  # Wait for 4 seconds
                await response.delete()  # Delete the bot's response after 4 seconds
                return  # Stop further processing

            # Check if the user has the trusted role
            trusted_role = discord.utils.get(message.guild.roles, name=trusted_role_name)
            if trusted_role and trusted_role not in message.author.roles:
                response = await message.channel.send(f" :warning: [ERROR] {message.author.mention} is not permitted to operate commands.")
                print(f"\033[95m{message.author} tried to use command '{message.content}' without trusted role\033[0m")
                await message.delete()  # Delete the invoker's message instantly
                await asyncio.sleep(4)  # Wait for 4 seconds
                await response.delete()  # Delete the bot's response after 4 seconds
                return  # Stop further processing

    # Check if the message does not start with the command prefix and is in admin-commands
    if not message.content.startswith(bot.command_prefix) and message.channel.name == "admin-commands":
        await message.delete()
        warning_msg = await message.channel.send(f'{message.author.mention}, you need to be using a command in this channel.')
        await asyncio.sleep(4)
        await warning_msg.delete()
        return  # Stop further processing for messages without prefix in admin-commands

    # Process commands here, including the setup command
    await bot.process_commands(message)
    await mock_message(message)




# Command : Create emoji command


@bot.command()
async def emojiadd(ctx, emoji_name: str, emoji_url: str):
    async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(emoji_url) as resp:
                    if resp.status != 200:
                        return await ctx.send('Failed to fetch image.')

                    emoji_bytes = await resp.read()
                    await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                    await ctx.send(f'Emoji `{emoji_name}` created successfully!')
            except aiohttp.ClientError as e:
                await ctx.send(f'Failed to create emoji: {e}')
            except discord.HTTPException as e:
                await ctx.send(f'Failed to create emoji: {e}')


# Command : remove emoji command
@bot.command()
@commands.has_permissions(manage_emojis=True)  # Check if the user has permission to manage emojis
async def emojiremove(ctx, emoji_name: str):
    try:
        emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name)
        if emoji:
            await emoji.delete()
            await ctx.send(f'Emoji `{emoji_name}` has been removed.')
        else:
            await ctx.send(f'Emoji `{emoji_name}` not found in the server.')
    except discord.Forbidden:
        await ctx.send('I do not have permission to manage emojis.')
    except discord.HTTPException as e:
        await ctx.send(f'Failed to remove emoji: {e}')

# Command : emoji info
@bot.command()
async def emoji(ctx, emoji_name: str):
    emoji = discord.utils.get(bot.emojis, name=emoji_name)
    if emoji:
        emoji_details = f'Emoji Name: {emoji.name}\nEmoji ID: {emoji.id}\nURL: {emoji.url}'
        await ctx.send(f'```{emoji_details}```')
    else:
        await ctx.send(f'Emoji `{emoji_name}` not found.')

# Command : Send dms command
@bot.command()
@commands.has_permissions(administrator=True)  # Restrict this command to users with admin permissions
async def senddm(ctx, user_reference: str, *, message: str):
    user = None

    # Check if the user_reference is a mention
    mention_match = re.match(r'<@!?(\d+)>', user_reference)
    if mention_match:
        user_id = int(mention_match.group(1))
        user = await bot.fetch_user(user_id)
    else:
        # Try to find user by ID
        try:
            user_id = int(user_reference)
            user = await bot.fetch_user(user_id)
        except ValueError:
            # Try to find user by username
            user = discord.utils.get(ctx.guild.members, name=user_reference)

    if user:
        try:
            await user.send(message)
            await ctx.send(f"Successfully sent a DM to {user.name}.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to send a DM to this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to send DM: {e}")
    else:
        await ctx.send("User not found.")


# Command : View dms command
@bot.command()
@commands.has_permissions(administrator=True)
async def viewdms(ctx, user_reference: str):
    user = None

    # Check if the user_reference is a mention
    mention_match = re.match(r'<@!?(\d+)>', user_reference)
    if mention_match:
        user_id = int(mention_match.group(1))
        user = await bot.fetch_user(user_id)
    else:
        # Try to find user by ID
        try:
            user_id = int(user_reference)
            user = await bot.fetch_user(user_id)
        except ValueError:
            # Try to find user by username or display name
            user = discord.utils.get(ctx.guild.members, name=user_reference)
            if not user:
                user = discord.utils.get(ctx.guild.members, display_name=user_reference)

    if user:
        try:
            # Open DM channel with the user
            dm_channel = await user.create_dm()
            # Fetch the last 10 messages from the DM channel
            messages = []
            async for message in dm_channel.history(limit=10):
                messages.append(message)

            if messages:
                history = "\n".join(
                    [f"{message.created_at} - {message.author}: {message.content}" for message in messages])
                await ctx.send(f"DM history with {user.name}:\n{history}")
            else:
                await ctx.send(f"No recorded DMs with {user.name}.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to view DMs with this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to fetch DMs: {e}")
    else:
        await ctx.send("User not found.")


# Aiohttp

# Global variable for aiohttp session
session = None

# Function to fetch data asynchronously
async def fetch_data(url):
    global session
    if session is None:
        session = aiohttp.ClientSession()
    async with session.get(url) as response:
        return await response.text()

# Command to force shutdown aiohttp session
@bot.command()
async def shutdown(ctx):
    global session
    if session:
        await session.close()
        session = None
        await ctx.send("aiohttp session closed.")
    else:
        await ctx.send("No active aiohttp session.")

# Example usage of fetch_data function
@bot.command()
async def fetch(ctx, url):
    try:
        html = await fetch_data(url)
        await ctx.send(f"HTML from {url}:\n{html}")
    except Exception as e:
        await ctx.send(f"Error fetching data from {url}: {e}")


# Run the event loop
async def main():
    await bot.start("YOUR_TOKEN_HERE")
    await cleanup()




@follow_user.before_loop
async def before_follow_user():
    await bot.wait_until_ready()  # Wait for the bot to be fully ready before starting the loop










# Run the main coroutine
bot.run(DISCORD_TOKEN)