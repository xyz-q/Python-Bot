import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from concurrent.futures import ThreadPoolExecutor 



youtube_dl.utils.bug_reports_message = lambda: ''

is_playing = False 
voice_client = None
queue = []
current_playing_url = None
loop_song = False
executor = ThreadPoolExecutor()  

ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'force_generic_extractor': False,
    'socket_timeout': 10,
    'retries': 10,
    'fragment_retries': 10
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
        self.ytdl_format_options = ytdl_format_options

    async def get_fresh_url(self, query):
        info = await self.download_info(query, self.ytdl_format_options)
        if info and 'entries' in info:
            return info['entries'][0]['url']
        return None

    async def download_info(self, query, ydl_opts):
        loop = asyncio.get_event_loop()
        ydl_opts['noplaylist'] = False 
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

        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and "Now playing:" in message.content:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
                break

        if not queue:
            voice_client = ctx.guild.voice_client
            if voice_client and voice_client.is_connected():
                await print("Queue is empty, cleaning up.")
            return

        next_query = queue.pop(0)
        author = ctx.message.author
        voice_channel = author.voice.channel if author.voice else None

        if not voice_channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            return

        voice_client = ctx.guild.voice_client
        
        try:
            fresh_url = await self.get_fresh_url(next_query)
            if fresh_url:
                current_playing_url = fresh_url
                info = await self.download_info(next_query, self.ytdl_format_options)
                if info and 'entries' in info:
                    title = info['entries'][0]['title']
                    
                    play_message = await ctx.send(f'Now playing: {title}')
                    
                    voice_client.play(
                        discord.FFmpegPCMAudio(
                            current_playing_url,
                            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                        ),
                        after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                    )
                    
                    controls = MusicControls(ctx, voice_client)
                    await play_message.edit(view=controls)
            else:
                await ctx.send("Could not get a valid URL for the next song.")
        except Exception as e:
            await ctx.send(f"An error occurred while playing the next song: {str(e)}")

    @commands.command()
    async def play(self, ctx, *, query):
        global queue, current_playing_url, is_playing

        print(f"Received play command with query: {query}")

        author = ctx.message.author
        voice_channel = author.voice.channel if author.voice else None

        if not voice_channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            print("User not in a voice channel.")
            return

        voice_client = ctx.guild.voice_client

        try:
            if voice_client and voice_client.is_connected():
                await voice_client.move_to(voice_channel)
                print("Moved to the user's voice channel.")
            else:
                voice_client = await voice_channel.connect()
                print("Connected to the user's voice channel.")
        except Exception as e:
            await ctx.send(f"Couldn't connect to voice channel: {str(e)}")
            print(f"Error connecting to voice channel: {str(e)}")
            return

        playlist_options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'extract_flat': False,
            'noplaylist': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extract_flat': 'in_playlist',
            'playliststart': 1,
            'playlistend': None,
            'playlist_items': None,
            'dump_single_json': True,
            'force_generic_extractor': False
        }

        try:
            await ctx.send("Fetching playlist information... This might take a moment.")
            print("Fetching playlist information...")

            ydl = youtube_dl.YoutubeDL(playlist_options)

            with ydl:
                result = await self.bot.loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, download=False)
                )

            if not result:
                await ctx.send("Could not fetch playlist information.")
                print("Could not fetch playlist information.")
                return

            if 'entries' in result:
                entries = list(result['entries'])
                playlist_title = result.get('title', 'Unknown Playlist')

                if not entries:
                    await ctx.send("No videos found in playlist.")
                    print("No videos found in playlist.")
                    return

                await ctx.send(f'Processing playlist: {playlist_title} ({len(entries)} tracks)')
                print(f'Processing playlist: {playlist_title} ({len(entries)} tracks)')

                for i, entry in enumerate(entries):
                    if entry is None:
                        continue

                    title = entry.get('title', 'Unknown Title')
                    video_url = entry.get('url', entry.get('webpage_url'))

                    if i == 0 and not (voice_client.is_playing() or is_playing):
                        download_msg = await ctx.send(f'Downloading: {title}')
                        await asyncio.sleep(2)
                        await download_msg.delete()

                        play_message = await ctx.send(f'Now playing: {title}')
                        print(f'Now playing: {title}')

                        try:
                            fresh_url = await self.get_fresh_url(video_url)
                            current_playing_url = fresh_url if fresh_url else video_url

                            is_playing = True
                            voice_client.play(
                                discord.FFmpegPCMAudio(
                                    current_playing_url,
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                                ),
                                after=lambda _: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                            )

                            controls = MusicControls(ctx, voice_client)
                            await play_message.edit(view=controls)
                        except Exception as e:
                            is_playing = False
                            await ctx.send(f"Error playing {title}: {str(e)}")
                            print(f"Error playing {title}: {str(e)}")
                    else:
                        queue.append(video_url)
                        print(f'Added to queue: {title}')

            else:
                title = result.get('title', 'Unknown Title')
                download_msg = await ctx.send(f'Downloading: {title}')
                await asyncio.sleep(2)

                if voice_client.is_playing() or is_playing:
                    queue.append(query)
                    await ctx.send(f'Added to queue: {title}')
                    await download_msg.delete()
                    print(f'Added to queue: {title}')
                else:
                    await download_msg.delete()
                    play_message = await ctx.send(f'Now playing: {title}')
                    print(f'Now playing: {title}')

                    try:
                        fresh_url = await self.get_fresh_url(query)
                        current_playing_url = fresh_url if fresh_url else result.get('url')

                        is_playing = True
                        voice_client.play(
                            discord.FFmpegPCMAudio(
                                current_playing_url,
                                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                            ),
                            after=lambda _: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                        )

                        controls = MusicControls(ctx, voice_client)
                        await play_message.edit(view=controls)
                    except Exception as e:
                        is_playing = False
                        await ctx.send(f"An error occurred while playing: {str(e)}")
                        print(f"An error occurred while playing: {str(e)}")
                        return

            if not voice_client.is_playing() and not is_playing:
                print("Nothing is playing, starting the next song in the queue.")
                await self.play_next(ctx)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error details: {str(e)}")
            return

    async def play_next(self, ctx):
        global queue, current_playing_url, is_playing

        print("Attempting to play next song in queue...")

        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and "Now playing:" in message.content:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
                break

        if not queue:
            voice_client = ctx.guild.voice_client
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                print("Queue is empty, disconnected from voice channel.")
            is_playing = False
            return

        next_query = queue.pop(0)
        author = ctx.message.author
        voice_channel = author.voice.channel if author.voice else None

        if not voice_channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            print("User not in a voice channel.")
            return

        voice_client = ctx.guild.voice_client

        retries = 3
        for attempt in range(retries):
            try:
                fresh_url = await self.get_fresh_url(next_query)
                if fresh_url:
                    current_playing_url = fresh_url
                    info = await self.download_info(next_query, self.ytdl_format_options)
                    if info and 'entries' in info:
                        title = info['entries'][0]['title']
                        
                        play_message = await ctx.send(f'Now playing: {title}')
                        print(f'Now playing: {title}')
                        
                        voice_client.play(
                            discord.FFmpegPCMAudio(
                                current_playing_url,
                                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                            ),
                            after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                        )
                        
                        controls = MusicControls(ctx, voice_client)
                        await play_message.edit(view=controls)
                        is_playing = True
                        return
                else:
                    await ctx.send("Could not get a valid URL for the next song.")
                    print("Could not get a valid URL for the next song.")
                    return
            except youtube_dl.DownloadError as e:
                if "sign in to confirm you're not a bot" in str(e):
                    await ctx.send("The video requires user authentication. Please try another video.")
                    print("The video requires user authentication. Please try another video.")
                    return
                else:
                    print(f"DownloadError occurred: {str(e)}")
            except Exception as e:
                print(f"An error occurred while playing the next song: {str(e)}")
            
            print(f"Retrying... ({attempt + 1}/{retries})")
            await asyncio.sleep(2)

        await ctx.send("Failed to play the next song after multiple attempts.")
        print("Failed to play the next song after multiple attempts.")
        is_playing = False


    @commands.command()
    async def q(self, ctx):
        if not queue:
            await ctx.send('The queue is currently empty.')
        else:
            queue_list = []
            for index, query in enumerate(queue):
                info = await self.download_info(query, self.ytdl_format_options)
                if info and 'entries' in info:
                    title = info['entries'][0]['title']
                else:
                    title = query
                queue_list.append(f'{index + 1}. {title}')
            
            queue_display = '\n'.join(queue_list)
            await ctx.send(f'**Current Queue:**\n{queue_display}')



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

    async def cleanup(self, ctx):
        """Clean up messages and disconnect when done"""
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and ("Now playing:" in message.content):
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass




async def setup(bot):
    await bot.add_cog(YouTubeCommands(bot))
