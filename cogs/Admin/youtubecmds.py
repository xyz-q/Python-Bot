import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor

# Suppress noise about console usage from youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Global variables for queue and voice client
is_playing = False  # Initialize is_playing as False initially
voice_client = None
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
    'source_address': '0.0.0.0',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class MusicControls(discord.ui.View):
    def __init__(self, ctx, voice_client):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.voice_client = voice_client
        self.is_playing = False  

    @discord.ui.button(label="▶▐▐", style=discord.ButtonStyle.blurple)
    async def play_pause_button(self, interaction, button):
        if self.voice_client.is_playing():
            self.voice_client.pause()
            button.label = "Resume"
            self.is_playing = False 
            await interaction.response.send_message("Playback paused.")
        elif self.voice_client.is_paused():
            self.voice_client.resume()
            button.label = "Pause"
            self.is_playing = True 
            await interaction.response.send_message("Playback resumed.")
        else:
            await interaction.response.send_message("I'm not playing anything right now.")

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.red)
    async def skip_button(self, interaction, button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
            await interaction.response.send_message("Skipped the current song.")
            await self.play_next(self.ctx)
            self.is_playing = False  
        else:
            await interaction.response.send_message("I'm not playing anything right now.")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.gray)
    async def stop_button(self, interaction, button):
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
            await interaction.response.send_message("Stopped playback.")
            self.is_playing = False  
        else:
            await interaction.response.send_message("I'm not playing anything right now.")



class YouTubeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                play_message = await ctx.send(f'Now playing: {title}')
                current_playing_url = url
    
                def after_callback(error):
                    if error:
                        print(f"Error occurred during playback: {error}")
                        traceback.print_exception(type(error), error, error.__traceback__)
                    else:
                        asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
    
                try:
                    voice_client.play(discord.FFmpegPCMAudio(url), after=after_callback)
                except Exception as e:
                    print(f"Error occurred while playing audio: {e}")
                    traceback.print_exception(type(e), e, e.__traceback__)
    
                # Create and send the MusicControls view
                controls = MusicControls(ctx, voice_client)
                await play_message.edit(view=controls)
     
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
                play_message = await ctx.send(f'Now playing: {title}')
                current_playing_url = url
                voice_client.play(discord.FFmpegPCMAudio(url), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))

                # Create and send the MusicControls view
                controls = MusicControls(ctx, voice_client)
                await play_message.edit(view=controls)

    # Command to show the current queue
    @commands.command()
    async def q(self, ctx):
        if not queue:
            await ctx.send('The queue is currently empty.')
        else:
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
