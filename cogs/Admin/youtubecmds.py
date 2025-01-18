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

        # Cleanup previous message
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and "Now playing:" in message.content:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass
                break

        if not queue:
            # If queue is empty, perform final cleanup
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
                    
                    # Send new "Now playing" message with fresh controls
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

        # Check if user is in voice channel
        author = ctx.message.author
        voice_channel = author.voice.channel if author.voice else None

        if not voice_channel:
            await ctx.send('You need to be in a voice channel to use this command.')
            return

        voice_client = ctx.guild.voice_client

        # Connect to voice channel
        try:
            if voice_client and voice_client.is_connected():
                await voice_client.move_to(voice_channel)
            else:
                voice_client = await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Couldn't connect to voice channel: {str(e)}")
            return

        # Special options for playlist extraction
        playlist_options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'extract_flat': False,  # Changed to False to get full info
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
            
            # Create a new YTDL instance with playlist options
            ydl =   youtube_dl.YoutubeDL(playlist_options)
            
            # Extract playlist info
            with ydl:
                result = await self.bot.loop.run_in_executor(
                    None, lambda: ydl.extract_info(query, download=False)
                )

            if not result:
                await ctx.send("Could not fetch playlist information.")
                return

            if 'entries' in result:
                entries = list(result['entries'])
                playlist_title = result.get('title', 'Unknown Playlist')
                
                if not entries:
                    await ctx.send("No videos found in playlist.")
                    return

                await ctx.send(f'Processing playlist: {playlist_title} ({len(entries)} tracks)')

                # Process each video in the playlist
                for i, entry in enumerate(entries):
                    if entry is None:
                        continue

                    title = entry.get('title', 'Unknown Title')
                    video_url = entry.get('url', entry.get('webpage_url'))
                    
                    if i == 0 and not (voice_client.is_playing() or is_playing):
                        # Play first song immediately
                        download_msg = await ctx.send(f'Downloading: {title}')
                        await asyncio.sleep(2)
                        await download_msg.delete()
                        
                        play_message = await ctx.send(f'Now playing: {title}')
                        
                        try:
                            fresh_url = await self.get_fresh_url(video_url)
                            current_playing_url = fresh_url if fresh_url else video_url

                            is_playing = True
                            voice_client.play(
                                discord.FFmpegPCMAudio(
                                    current_playing_url,
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                                ),
                                after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                            )
                            
                            controls = MusicControls(ctx, voice_client)
                            await play_message.edit(view=controls)
                        except Exception as e:
                            is_playing = False
                            await ctx.send(f"Error playing {title}: {str(e)}")
                    else:
                        # Add other songs to queue
                        queue.append(video_url)
                        print(f'Added to queue: {title}')
                        

            else:
                # Handle single video
                title = result.get('title', 'Unknown Title')
                download_msg = await ctx.send(f'Downloading: {title}')
                await asyncio.sleep(2)

                if voice_client.is_playing() or is_playing:
                    queue.append(query)
                    await ctx.send(f'Added to queue: {title}')
                    await download_msg.delete()
                else:
                    await download_msg.delete()
                    play_message = await ctx.send(f'Now playing: {title}')
                    
                    try:
                        fresh_url = await self.get_fresh_url(query)
                        current_playing_url = fresh_url if fresh_url else result.get('url')
                        
                        is_playing = True
                        voice_client.play(
                            discord.FFmpegPCMAudio(
                                current_playing_url,
                                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                            ),
                            after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
                        )
                        
                        controls = MusicControls(ctx, voice_client)
                        await play_message.edit(view=controls)
                    except Exception as e:
                        is_playing = False
                        await ctx.send(f"An error occurred while playing: {str(e)}")
                        return

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error details: {str(e)}")
            return

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
                    title = query  # Fallback to raw query if title extraction fails
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
        # Remove "Now Playing" messages
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user and ("Now playing:" in message.content):
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass




async def setup(bot):
    await bot.add_cog(YouTubeCommands(bot))
