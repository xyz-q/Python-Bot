import os
import asyncio
import discord
from discord.ext import commands

class Mp3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.soundboard_dir = os.path.join(current_dir, '.mp3')

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

            mp3_files = [file for file in os.listdir(self.soundboard_dir) if file.endswith('.mp3')]
            matched_files = []
            for keyword in keywords:
                for mp3_file in mp3_files:
                    if keyword.lower() in mp3_file.lower():
                        matched_files.append(mp3_file)

            if not matched_files:
                await ctx.send("No matching mp3 files found.")
                return

            if len(matched_files) > 1:
                await ctx.send(f"Multiple matching files found: {', '.join(matched_files)}. Please specify a more specific keyword.")
                return

            mp3_file = os.path.join(self.soundboard_dir, matched_files[0])

            if not os.path.exists(mp3_file):
                await ctx.send(f"{matched_files[0]} file not found.")
                return

            if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(mp3_file))
                await ctx.send(f"Playing {matched_files[0]}.")
                while voice_client.is_playing():
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error playing mp3: {e}")
            await ctx.send("An error occurred while trying to play the mp3.")

    @commands.command()
    async def stop(self, ctx):
        await self.stop_audio(ctx)

    async def stop_audio(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Audio playback stopped.")
        else:
            await ctx.send("No audio is currently playing.")

import os
import asyncio
import discord
from discord.ext import commands

class Mp3(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.soundboard_dir = os.path.join(current_dir, '.mp3')

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

            mp3_files = [file for file in os.listdir(self.soundboard_dir) if file.endswith('.mp3')]
            matched_files = []
            for keyword in keywords:
                for mp3_file in mp3_files:
                    if keyword.lower() in mp3_file.lower():
                        matched_files.append(mp3_file)

            if not matched_files:
                await ctx.send("No matching mp3 files found.")
                return

            if len(matched_files) > 1:
                await ctx.send(f"Multiple matching files found: {', '.join(matched_files)}. Please specify a more specific keyword.")
                return

            mp3_file = os.path.join(self.soundboard_dir, matched_files[0])

            if not os.path.exists(mp3_file):
                await ctx.send(f"{matched_files[0]} file not found.")
                return

            if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(mp3_file))
                await ctx.send(f"Playing {matched_files[0]}.")
                while voice_client.is_playing():
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error playing mp3: {e}")
            await ctx.send("An error occurred while trying to play the mp3.")

    @commands.command()
    async def stop(self, ctx):
        await self.stop_audio(ctx)

    async def stop_audio(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Audio playback stopped.")
        else:
            await ctx.send("No audio is currently playing.")

    @commands.command()
    async def mp3list(self, ctx):
        if not os.path.exists(self.soundboard_dir):
            await ctx.send("The '.mp3' folder does not exist.")
            return
        sound_files = [file for file in os.listdir(self.soundboard_dir) if file.endswith('.mp3')]
        if not sound_files:
            await ctx.send("No .mp3 files found in the '.mp3' folder.")
            return
        embed = discord.Embed(title="Available MP3 Files", color=discord.Color.gold())
        song_list = "\n".join(sound_files)
        embed.description = song_list
        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Mp3(bot))



async def setup(bot):
    await bot.add_cog(Mp3(bot))
