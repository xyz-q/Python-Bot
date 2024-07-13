import discord
from discord.ext import commands, tasks
import requests
from discord import ui

class StreamButton(ui.View):
    def __init__(self, stream_url):
        super().__init__()
        self.add_item(ui.Button(label="Watch Stream", url=stream_url))

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_username = 'nolimitkryptik'
        self.discord_channel_id = 1261338143056072704
        self.twitch_client_id = 'gp762nuuoqcoxypju8c569th9wz7q5'
        self.twitch_access_token = 'j52x6xdpndzfihjjlv9mz2ty41v2mu'
        self.stream_status.start()
        self.load_previous_status()

    def load_previous_status(self):
        try:
            with open("previous_status.txt", "r") as f:
                self.previous_status = f.read().strip()
        except FileNotFoundError:
            self.previous_status = None

    def save_previous_status(self):
        with open("previous_status.txt", "w") as f:
            f.write(self.previous_status)

    def check_stream_status(self):
        url = f"https://api.twitch.tv/helix/streams?user_login={self.twitch_username}"
        headers = {
            "Client-ID": self.twitch_client_id,
            "Authorization": f"Bearer {self.twitch_access_token}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        if data["data"]:
            stream_data = data["data"][0]
            return stream_data
        else:
            return None

    @tasks.loop(seconds=60)
    async def stream_status(self):
        channel = self.bot.get_channel(self.discord_channel_id)
        if channel is None:
            print(f"Error: Discord channel with ID {self.discord_channel_id} not found.")
            return

        is_live = self.check_stream_status()

        if is_live:
            title = is_live.get('title', 'No title available')
            category = is_live.get('game_name', 'No category available')
            if self.previous_status != 'live':
                stream_url = f"https://www.twitch.tv/{self.twitch_username}"
                embed.add_field(name="Title", value=title, inline=False)
                embed.add_field(name="Category", value=category, inline=False)
                embed.set_thumbnail(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{self.twitch_username}-320x180.jpg")
                stream_button = StreamButton(stream_url)
                await channel.send("@here", embed=embed, view=stream_button)
                self.previous_status = 'live'
                self.save_previous_status()
        else:
            if self.previous_status != 'offline':
                twitch_channel_url = f"https://www.twitch.tv/{self.twitch_username}"
                embed = discord.Embed(title=f"{self.twitch_username} is currently offline", url=twitch_channel_url, color=0xFF0000)
                await channel.send(embed=embed)
                self.previous_status = 'offline'
                self.save_previous_status()

    @commands.command()
    async def twitch(self, ctx):
        """Check if the Twitch stream is live"""
        is_live = self.check_stream_status()

        if is_live:
            title = is_live.get('title', 'No title available')
            category = is_live.get('game_name', 'No category available')
            if self.previous_status != 'live':
                stream_url = f"https://www.twitch.tv/{self.twitch_username}"
                embed.add_field(name="Title", value=title, inline=False)
                embed.add_field(name="Category", value=category, inline=False)
                embed.set_thumbnail(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{self.twitch_username}-320x180.jpg")
                stream_button = StreamButton(stream_url)
                await ctx.send("@here", embed=embed, view=stream_button)
                self.previous_status = 'live'
                self.save_previous_status()
        else:
            if self.previous_status != 'offline':
                twitch_channel_url = f"https://www.twitch.tv/{self.twitch_username}"
                embed = discord.Embed(title=f"{self.twitch_username} is currently offline", url=twitch_channel_url, color=0xFF0000)
                await ctx.send(embed=embed)
                self.previous_status = 'offline'
                self.save_previous_status()

async def setup(bot):
    await bot.add_cog(Twitch(bot))
