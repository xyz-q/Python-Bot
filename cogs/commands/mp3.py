import os
import asyncio
import discord
from discord.ext import commands

class Mp3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command: `mp3`
    @commands.command()
    async def mp3(self, ctx, *keywords: str):
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
            soundboard_dir = os.path.join(current_dir, '.mp3')

            # Get all mp3 files in the .mp3 directory
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
                await ctx.send(f"{matched_files[0]} file not found in the .mp3 file.")
                return

            if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(mp3_file))
                await ctx.send(f"Playing {matched_files[0]}.")
                while voice_client.is_playing():
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error playing mp3: {e}")
            await ctx.send("An error occurred while trying to play the mp3.")

    # Command: Stop mp3
    @commands.command()
    async def stop(self, ctx):
        await self.stop_audio(ctx)

    async def stop_audio(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Audio playback stopped.")
        else:
            await ctx.send("No audio is currently playing.")

    # Command: List mp3 files
    @commands.command()
    async def mp3list(self, ctx):
        # Path to the '.mp3' folder
        soundboard_folder = '.mp3'

        # Check if the '.mp3' folder exists
        if not os.path.exists(soundboard_folder):
            await ctx.send("The '.mp3' folder does not exist.")
            return

        # Get a list of all files in the '.mp3' folder
        sound_files = [file for file in os.listdir(soundboard_folder) if file.endswith('.mp3')]

        # Check if there are no .mp3 files in the '.mp3' folder
        if not sound_files:
            await ctx.send("No .mp3 files found in the '.mp3' folder.")
            return

        # Send the list of .mp3 files
        await ctx.send("List of available songs:")
        for song in sound_files:
            await ctx.send(song)

async def setup(bot):
    await bot.add_cog(Mp3(bot))
