import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio

class TextToSpeech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tts_enabled_users = set()

    @commands.command(name="tts", aliases=['t'])
    @commands.is_owner()
    async def toggletts(self, ctx):
        """Toggles TTS mode for the bot owner"""
        if ctx.author.id in self.tts_enabled_users:
            self.tts_enabled_users.remove(ctx.author.id)
            await ctx.send("TTS mode disabled", delete_after=3)
        else:
            self.tts_enabled_users.add(ctx.author.id)
            await ctx.send("TTS mode enabled", delete_after=3)
        
        try:
            await ctx.message.delete()
        except discord.errors.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content.startswith(','):
            return

        if message.author.id not in self.tts_enabled_users:
            return

        if not message.author.voice:
            return

        voice_channel = message.author.voice.channel
        voice_client = message.guild.voice_client

        try:
            if not voice_client:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

            tts = gTTS(text=message.content, lang='en')
            temp_file = f'tts_{message.id}.mp3'
            tts.save(temp_file)

            if voice_client.is_playing():
                voice_client.stop()

            def after_playing(error):
                if error:
                    print(f'Error in playback: {error}')
                asyncio.run_coroutine_threadsafe(
                    self.cleanup(temp_file, message), 
                    self.bot.loop
                )

            voice_client.play(
                discord.FFmpegPCMAudio(temp_file),
                after=after_playing
            )

        except Exception as e:
            print(f"Error in TTS: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    async def cleanup(self, file_path, message):
        await asyncio.sleep(1)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            await message.delete()
        except Exception as e:
            print(f"Cleanup error: {e}")

async def setup(bot):
    await bot.add_cog(TextToSpeech(bot))