import discord
from discord import FFmpegPCMAudio
from discord import app_commands
import discord.ext.commands as commands
from dotenv import load_dotenv
# import youtube-dl
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
    (",dnd", "Toggles the bot between DnD and Idle Mode"),
    (",disconnect <@user>", "Disconnect user from a voice channel"),
    (",drag <@user>", " Move a user to a voice channel"),
    (",deafen <@user>", "Deafens the target user, if none is specified it deafens the bot"),
    (",gather <#channel>", "Moves all users into the voice channel that you are in or the channel specified."),
    (",join <channel-name> (optional)", "Joins the channel you're in, or if specified it joins the channel name"),
    (",jail <@user>", "Assigns the user to the '.jail' role"),
    (",kill ", " KILLS THE BOT [restricted command] "),
    (",kick <@user(s)> {reason}", "Kicks the user(s) from the server"),
    (",leave", "Leaves the channel the bot is in"),
    (",mock <@user>", "Mocks target user(s)"),
    (",mute <@user>", "Mutes target user"),
    (",names <@user>", "Gets the old nicknames of a user"),
    (",online ", "Sets bot status as 'Online'"),
    (",offline", "Sets bot status as 'Offline'"),
    (",play <URL>", "Plays youtube URL"),
    (",playmp3 <mp3>", "Plays Target MP3"),
    (",mp3list ", "Shows a list of mp3s in the file"),
    (",ping", "Ping command - Test if the bot is responsive- displays the latency from the bot to the server"),
    (",purge <#channel/number> <number>", "Deletes messages in #channel if specified, default is 100"),
    (",release <@user>", "Releases the user from the '.jail' role"),
    (",resetstatus", "Resets the bot's status"),
    (",stalk <@user>", "Stalks the specified user"),
    (",stopstalk", "Stops stalking selected user"),
    (",setstatus <activity-type> <status>", "Sets the bot's status"),
    (",say <#channel> 'TEXT'' ", "Makes the bot chat the desired text in specified channel"),
    ("/ticket", "Creates a ticket"),
    (",user <@user>", "Displays info on user"),
    (",volume <1-100>", "Sets the bot's volume"),
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
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument.")
    else:
        await ctx.send("An error occurred.")
        print(f"An error occurred: {error}")

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


# Command to leave the voice channel
@bot.command()
async def leave(ctx):
    # Check if the bot is connected to a voice channel
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.send("I'm not connected to a voice channel.")
        return

    # Disconnect from the voice channel
    await voice_client.disconnect()
    await ctx.send("Left the voice channel.")

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
        await ctx.send("The specified user is not in a voice channel, or the bot isn't in a voice channel. Starting the loop anyway...")
        print(f"Started stalking {member.display_name} even though they are not in a voice channel.")

    followed_user = member
    await ctx.send(f"Now stalking {member.display_name} in {voice_channel.name}.", delete_after=5)
    print(f"\033[30mNow stalking\033[0m \033[91m{member.display_name}\033[0m \033[30min\033[0m \033[91m{voice_channel.name}\033[0m.")
    await ctx.message.delete(delay=5)

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


 # UPDATE

# Event : Auto play sound
@bot.event
async def on_voice_state_update(member, before, after):
    # Check if the member is the bot itself
    if member == bot.user:
        # Check if the bot moved to a voice channel
        if before.channel != after.channel:
            if after.channel is not None:
                # Bot joined a voice channel
                print(f"The bot has joined voice channel: {after.channel.name}")
                # Add your actions here, such as playing a welcome message or music
            else:
                # Bot left a voice channel
                print("The bot has left voice channel.")
                # Add your cleanup actions here, if necessary

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


# Event : Auto play sound
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



# Event : Play mp3 on join [ autoplay ]
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

# Command to play audio from YouTube link
@bot.command()
async def play(ctx, url: str):
    # Check if the user is in a voice channel
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    # Connect to the voice channel
    voice_channel = ctx.author.voice.channel
    voice_client = ctx.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()

    # Download audio from YouTube link
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.mp3',  # Save the audio as 'audio.mp3'
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Play the downloaded audio
    voice_client.play(discord.FFmpegPCMAudio('audio.mp3'))

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

    # Determine the channel to purge messages from
    if channel is None:
        channel = ctx.channel

    # Delete messages
    deleted = await channel.purge(limit=limit)
    await ctx.send(f"Purged {len(deleted)} message(s) from {channel.mention}.")

# Modal: ticket modal
class TicketModal(discord.ui.Modal, title="Ticket Submission"):
    subject = discord.ui.TextInput(label="Subject", style=discord.TextStyle.short, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        subject = self.subject.value
        description = self.description.value

        # Assuming 'tickets' channel exists
        ticket_channel = discord.utils.get(interaction.guild.text_channels, name="tickets")

        if ticket_channel is not None:
            embed = discord.Embed(title="New Ticket", color=discord.Color.blue())
            embed.add_field(name="Subject", value=subject, inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Submitted by", value=interaction.user.name, inline=False)  # Changed to use username

            view = TicketButtons(interaction.user, subject, description)

            await ticket_channel.send(embed=embed, view=view)
            await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True)
        else:
            await interaction.response.send_message("Ticket channel not found. Please contact an administrator.",
                                                    ephemeral=True)


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

        embed = discord.Embed(title="Ticket Details", color=discord.Color.blue())
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


# Role ID to assign when a user is accepted
ROLE_ID = 1056996133081186395  # Replace with the role ID you want to assign

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
            await self.message.delete()  # Delete the original message

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.user.kick(reason="Declined membership.")
        await self.user.send("Access to the server has been declined by an Admin.")
        await self.message.delete()  # Delete the original message

# Function to send a ticket message
async def send_ticket_message(member: discord.Member, guild: discord.Guild):
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
    else:
        print("Error: Could not find the specified channel for ticket messages.")


async def send_welcome_message(member: discord.Member):
    # Find the channel to send the welcome message
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name=WELCOME_CHANNEL_NAME, type=discord.ChannelType.text)
        if channel:
            break

    if channel:
        # Create an embed for the welcome message
        embed = discord.Embed(
            title=f"{member.display_name} pulled up",
            description=f"Username: {member.name}",
            color=discord.Color.red()
        )

        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text=f"User ID: {member.id}")

        # Send the welcome message
        await channel.send(embed=embed)
    else:
        print("Error: Could not find the specified channel for welcome messages.")




# Event to detect when a member joins the server
@bot.event
async def on_member_join(member: discord.Member):
    await send_welcome_message(member)
    await send_ticket_message(member, member.guild)


# Event: Farewell message
@bot.event
async def on_member_remove(member):
    # Find the channel to send the farewell message
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name="exit", type=discord.ChannelType.text)
        if channel:
            break

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
            await warning_message.edit(content=":orange_circle: Bot TERMINATION cancelled due to inactivity.")
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


# Event : Check for user Role/Channel status
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore messages sent by the bot itself

    # Check if the message is a command
    if message.content.startswith(bot.command_prefix):
        # Check if the message is not the setup command
        if not message.content.startswith(bot.command_prefix + "list"):
            # Check if the message is not from the allowed channel
            if message.channel.name != allowed_channel_name:
                error_message = ":warning: Commands can only be used in the #admin-commands channel. [/setup]"
                response = await message.channel.send(error_message)
                print(f"\033[95m{message.author} Tried to activate command in another channel\033[0m")
                await message.delete()  # Delete the invoker's message instantly
                await asyncio.sleep(4)  # Wait for 4 seconds
                await response.delete()  # Delete the bot's response after 4 seconds
                return  # Stop further processing

            # Check if the user has the trusted role
            trusted_role = discord.utils.get(message.guild.roles, name=trusted_role_name)
            if trusted_role not in message.author.roles:
                response = await message.channel.send(f" :warning: [ERROR] {message.author.mention} is not permitted to operate commands.")
                print(f"\033[95m{message.author} tried to use command '{message.content}' without trusted role\033[0m")
                await message.delete()  # Delete the invoker's message instantly
                await asyncio.sleep(4)  # Wait for 4 seconds
                await response.delete()  # Delete the bot's response after 4 seconds
                return  # Stop further processing

    # Check if the message is sent in the admin-commands channel
    if message.channel.name == "admin-commands":
        # Check if the message is sent by a bot
        if message.author.bot:
            return

        # Check if the message starts with the command prefix
        command_prefix = ","  # Change this to your command prefix
        if not message.content.startswith(command_prefix):
            # Delete the invoker's message
            await message.delete()

            # Send a warning message
            warning_message = f"Warning: Message by {message.author.mention} in admin-commands channel doesn't start with the command prefix!  ','"
            warning_response = await message.channel.send(warning_message)

            # Delay the bot's response by 4 seconds
            await asyncio.sleep(4)

            # Delete the warning message
            await warning_response.delete()




    # Check if user is typing in the status channel
    if message.channel.id == 1234310879072223292 and not message.author.bot:
        await message.delete()
        warning_msg = await message.channel.send(
            f'{message.author.mention}, sending messages in this channel is not allowed.')
        await asyncio.sleep(4)
        await warning_msg.delete()

    # Check if the mentioned user(s) are AFK
    mentioned_afk_users = [user_id for user_id in afk_users if
                            message.guild.get_member(int(user_id)) in message.mentions]
    if mentioned_afk_users:
        for user_id in mentioned_afk_users:
            reason = afk_users[user_id]
            user = message.guild.get_member(int(user_id))
            await message.channel.send(f"{user.mention} is currently AFK. Reason: {reason}")


    # Process commands here, including the setup command
    await bot.process_commands(message)
    await mock_message(message)



# Event
# Run the event loop




# Async run
async def main():
    await bot.start("YOUR_TOKEN_HERE")
    await cleanup()

@follow_user.before_loop
async def before_follow_user():
    await bot.wait_until_ready()  # Wait for the bot to be fully ready before starting the loop










# Run the main coroutine
bot.run(DISCORD_TOKEN)