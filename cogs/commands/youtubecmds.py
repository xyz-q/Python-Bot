import asyncio
import discord
from discord.ext import commands
#import youtube_dl
from concurrent.futures import ThreadPoolExecutor
import yt_dlp as youtube_dl

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

class YouTubeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command to play audio from YouTube link
    @commands.command()
    async def youtube(self, ctx, *, query):
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

    # Command to play audio from YouTube with queue support
    @commands.command()
    async def play(self, ctx, *, query):
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

            if voice_client.is_playing() or is_playing:
                queue.append(query)
                await ctx.send(f'Added to queue: {title}')
                await download_msg.delete()  # Delete download message if added to queue
            else:
                await download_msg.delete()  # Delete download message if starting to play now
                await ctx.send(f'Now playing: {title}')
                current_playing_url = url
                voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        else:
            await ctx.send(f'No video found for query: {query}')

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

    async def play_next(self, ctx):
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

            info = await self.download_info(next_query, ydl_opts)
            if info is None:
                await ctx.send(f'No video found for query: {next_query}')
                return

            if 'entries' in info:
                video = info['entries'][0]
                url = video['url']
                title = video['title']
                await ctx.send(f'Now playing: {title}')
                current_playing_url = url
                voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))

    # Command to show the current queue
    @commands.command()
    async def q(self, ctx):
        if not queue:
            await ctx.send('The queue is currently empty.')
        else:
            queue_list = '\n'.join([f'{index + 1}. {item}' for index, item in enumerate(queue)])
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

    # Command to pause playback
    @commands.command()
    async def pause(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send('Playback paused.')
        else:
            await ctx.send("I'm not playing anything right now.")

    # Command to resume playback
    @commands.command()
    async def resume(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send('Playback resumed.')
        else:
            await ctx.send("I'm not paused right now.")

    # Command to skip current song
    @commands.command()
    async def skip(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send('Skipped the current song.')
            await self.play_next(ctx)
        else:
            await ctx.send("I'm not playing anything right now.")

    # Command to make the bot leave the voice channel
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
