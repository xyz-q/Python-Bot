import nextcord as discord
from nextcord.ext import commands
import asyncio
import os
from datetime import datetime
import wave

class UserRecorderSink(discord.AudioSink):
    def __init__(self, recorder, user_id):
        self.recorder = recorder
        self.user_id = user_id

    def write(self, data: discord.AudioData):
        if data.user.id == self.user_id:
            pcm_data = data.pcm
            self.recorder.recording_users[self.user_id]['audio_data'].append(pcm_data)

class VoiceRecorder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recording_users = {}
        self.recordings_dir = os.path.abspath("recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)
        print(f"Recordings directory: {self.recordings_dir}")

    @commands.command()
    @commands.is_owner()
    async def record_user(self, ctx, user: discord.Member, duration: int = 30):
        """Record a specific user's audio from voice channel"""
        if not user.voice:
            await ctx.send(f"{user.name} is not in a voice channel!")
            return

        if user.id in self.recording_users:
            await ctx.send(f"Already recording {user.name}!")
            return

        voice_channel = user.voice.channel
        vc = ctx.voice_client

        if vc is None:
            try:
                vc = await voice_channel.connect()
            except discord.ClientException as e:
                await ctx.send(f"Error connecting to voice channel: {str(e)}")
                return
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.recordings_dir, f"{user.name}_{timestamp}.wav")

        # Initialize recording session
        self.recording_users[user.id] = {
            'filename': filename,
            'audio_data': [],
            'start_time': datetime.now()
        }

        vc.listen(UserRecorderSink(self, user.id))
        await ctx.send(f"🎙️ Started recording {user.name} for {duration} seconds...")

        await asyncio.sleep(duration)
        await self.stop_recording_user(ctx, user)

    async def stop_recording_user(self, ctx, user: discord.Member):
        if user.id not in self.recording_users:
            return

        recording_data = self.recording_users.pop(user.id)
        filename = recording_data['filename']
        audio_data = recording_data['audio_data']

        if ctx.voice_client:
            ctx.voice_client.stop_listening()
            await ctx.voice_client.disconnect()

        if audio_data:
            try:
                self.save_wav(filename, audio_data)

                file_size = os.path.getsize(filename)
                if file_size > 0:
                    await ctx.send(
                        f"Recording of {user.name} saved! File size: {file_size} bytes",
                        file=discord.File(filename)
                    )
                else:
                    await ctx.send(f"Warning: Recording of {user.name} is empty (0 bytes)")
            except Exception as e:
                await ctx.send(f"Error saving recording: {str(e)}")
        else:
            await ctx.send(f"No audio was recorded for {user.name}")

    @staticmethod
    def save_wav(filename, audio_data, channels=2, sampwidth=2, framerate=48000):
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(b''.join(audio_data))

    @commands.command()
    @commands.is_owner()
    async def stop_recording(self, ctx, user: discord.Member):
        if user.id not in self.recording_users:
            await ctx.send(f"Not currently recording {user.name}!")
            return

        await self.stop_recording_user(ctx, user)
        await ctx.send(f"Stopped recording {user.name}")

    @commands.command()
    @commands.is_owner()
    async def listrecordings(self, ctx):
        try:
            files = os.listdir(self.recordings_dir)
            if not files:
                await ctx.send("No recordings found!")
                return

            recordings_list = "\n".join(files)
            await ctx.send(f"Recordings:\n```{recordings_list}```")
        except Exception as e:
            await ctx.send(f"Error listing recordings: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.recording_users and (not after.channel or after.channel != before.channel):
            ctx = await self.bot.get_context(member.last_message) if member.last_message else None
            if ctx:
                await self.stop_recording_user(ctx, member)

async def setup(bot):
    await bot.add_cog(VoiceRecorder(bot))
