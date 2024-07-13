import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from concurrent.futures import ThreadPoolExecutor

# Suppress noise about console usage from youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Global variables for queue and voice client
queue = []
current_playing_url = None
loop_song = False
executor = ThreadPoolExecutor()  # Create an instance of ThreadPoolExecutor

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

class MusicControls(discord.ui.View):
    def __init__(self, ctx, voice_client, queue):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.voice_client = voice_client
        self.queue = queue
        self.bot = bot 
        self.is_playing = False
        self.play_pause_button = self.children[0]

    async def play_next(self):
        if self.queue:
            url = self.queue.pop(0)
            self.voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop).result())
            self.is_playing = True
            self.play_pause_button.emoji = "\u23F8"  # Pause emoji

    @discord.ui.button(emoji="\u25B6\uFE0F", style=discord.ButtonStyle.blurple)  # Play emoji
    async def play_pause_button(self, interaction, button):
        await interaction.response.defer()  # Defer the interaction response

        if self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_playing = False
            button.emoji = "\u25B6\uFE0F"  # Play emoji
        else:
            if self.voice_client.is_paused():
                self.voice_client.resume()
                self.is_playing = True
                button.emoji = "\u23F8"  # Pause emoji
            else:
                await self.play_next()
        await interaction.message.edit(view=self)  # Update the message with the new button state

    @discord.ui.button(emoji="\u23ED", style=discord.ButtonStyle.red)  # Skip emoji
    async def skip_button(self, interaction, button):
        await interaction.response.defer()  # Defer the interaction response

        if self.voice_client.is_playing():
            self.voice_client.stop()
            await self.play_next()
        await interaction.message.edit(view=self)  # Update the message with the new button state

    @discord.ui.button(emoji="\u23F9", style=discord.ButtonStyle.gray)  # Stop emoji
    async def stop_button(self, interaction, button):
        await interaction.response.defer()  # Defer the interaction response

        if self.voice_client.is_playing():
            self.voice_client.stop()
            self.is_playing = False
            self.play_pause_button.emoji = "\u25B6\uFE0F"  # Play emoji
            self.queue.clear()
        await interaction.message.edit(view=self)  # Update the message with the new button state

class YouTubeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, ctx, voice_client):
        if queue:
            url = queue.pop(0)
            voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx, voice_client), self.bot.loop).result())
            controls = MusicControls(ctx, voice_client, queue)
            await ctx.send(view=controls)
        else:
            await ctx.send("Queue is empty.")

    async def download_info(self, query, ydl_opts):
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

    @commands.command()
    async def play(self, ctx, *, query):
        global queue, current_playing_url

        author = ctx.message.author
        voice_channel = author.voice.channel

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

        info = await self.download_info(query, ydl_opts)
        if info is None:
            await ctx.send(f'No video found for query: {query}')
            return

        if 'entries' in info:
            video = info['entries'][0]
            url = video['url']
            title = video['title']

            download_msg = await ctx.send(f'Downloading: {title}')
            await asyncio.sleep(4)  # Simulate downloading delay

            if voice_client.is_playing() or queue:
                queue.append(url)
                await ctx.send(f'Added to queue: {title}')
                await download_msg.delete()  # Delete download message if added to queue
            else:
                await download_msg.delete()  # Delete download message if starting to play now
                play_message = await ctx.send(f'Now playing: {title}')
                current_playing_url = url

                # Create an instance of MusicControls
                controls = MusicControls(ctx, voice_client, queue)

                # Start playing the audio and call play_next on the YouTubeCommands instance
                voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx, voice_client), self.bot.loop).result())

                # Send the MusicControls view
                await play_message.edit(view=controls)

    # Command to show the current queue
    @commands.command()
    async def q(self, ctx):
        if not queue:
            await ctx.send('The queue is currently empty.')
        else:
            queue_list = '\n'.join(f'{i+1}. {queue[i]}' for i in range(len(queue)))
            await ctx.send(f'**Current Queue:**\n{queue_list}')

    # Command to clear the queue
    @commands.command()
    async def clearq(self, ctx):
        global queue
        if not queue:
            await ctx.send('The queue is already empty.')
        else:
            queue.clear()
            await ctx.send('Queue cleared.')

    @commands.command()
    async def leave(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            queue.clear()
        else:
            await ctx.send("I'm not connected to any voice channel.")

async def setup(bot):
    await bot.add_cog(YouTubeCommands(bot))
