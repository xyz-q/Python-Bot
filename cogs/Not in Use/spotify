import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import discord
from discord.ext import commands
import asyncio

class SpotifyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri='http://localhost:8080',
            scope='user-modify-playback-state'
        ))

    @commands.command()
    async def play(self, ctx, *, query: str):
        try:
        # Check if the user is in a voice channel
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("You must be in a voice channel to use this command.")
                return

        # Check if the bot is already connected to a voice channel
            if ctx.voice_client:
            # If the bot is already connected, move it to the user's voice channel
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            else:
            # If the bot is not connected, connect it to the user's voice channel
                voice_channel = ctx.author.voice.channel
                await voice_channel.connect()

        # Search for the song/artist/playlist
            results = self.sp.search(q=query, type='track')
            track_uri = results['tracks']['items'][0]['uri']

        # Get the audio stream from Spotify
            track = self.sp.track(track_uri)
            audio_url = track['preview_url']

        # Play the audio through the Discord voice channel
            source = discord.FFmpegPCMAudio(audio_url)
            ctx.voice_client.play(source)
            await ctx.send(f'Now playing: {results["tracks"]["items"][0]["name"]}')

        # Wait for the song to finish playing
            while ctx.voice_client.is_playing():
                await asyncio.sleep(1)

        # Disconnect the bot from the voice channel
            await ctx.voice_client.disconnect()

        except Exception as e:
            await ctx.send(f'Error playing Spotify track: {e}')

async def setup(bot):
    await bot.add_cog(SpotifyCommands(bot))
