import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio

class TextToSpeech(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}

    @commands.command(aliases=['t'])
    async def tts(self, ctx, *, text):
        """Converts text to speech and plays it in the voice channel"""
        # Store the original message for later deletion
        original_message = ctx.message
        
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("You need to be in a voice channel first!")
                return
            await ctx.author.voice.channel.connect()

        try:
            # Create TTS file
            tts = gTTS(text=text, lang='en')
            temp_file = f'tts_{ctx.message.id}.mp3'
            tts.save(temp_file)

            # Play the audio
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            def after_playing(error):
                if error:
                    print(f'Error in playback: {error}')
                # Use create_task to properly run the cleanup coroutine
                asyncio.run_coroutine_threadsafe(self.cleanup_file(temp_file, original_message), self.bot.loop)

            audio_source = discord.FFmpegPCMAudio(temp_file)
            ctx.voice_client.play(audio_source, after=after_playing)

        except Exception as e:
            await ctx.send(f"Error creating TTS: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            # Delete the command message even if there's an error
            try:
                await original_message.delete()
            except discord.errors.HTTPException:
                pass

    async def cleanup_file(self, file_path, message):
        """Cleanup temporary files and remove the command message"""
        await asyncio.sleep(1)  # Wait a bit to ensure the file is no longer in use
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            
            # Delete the command message
            try:
                await message.delete()
                print(f"Deleted message: {message.content}")
            except discord.errors.HTTPException as e:
                print(f"Error deleting message: {e}")
                
        except Exception as e:
            print(f"Error in cleanup: {e}")

async def setup(bot):
    await bot.add_cog(TextToSpeech(bot))
