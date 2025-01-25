import discord
from discord.ext import commands, tasks
import requests
from discord import ui
import json


class StreamButton(ui.View):
    def __init__(self, stream_url):
        super().__init__()
        self.add_item(ui.Button(label="Watch Stream", url=stream_url))

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.configurations = self.load_configurations()
        self.stream_status.start()

    def load_configurations(self):
        try:
            with open('.json/ttv.json', 'r') as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_configurations(self):
        with open('.json/ttv.json', 'w') as file:
            json.dump(self.configurations, file, indent=4)

    def check_stream_status(self, twitch_username, twitch_client_id, twitch_access_token):
        url = f"https://api.twitch.tv/helix/streams?user_login={twitch_username}"
        headers = {
            "Client-ID": twitch_client_id,
            "Authorization": f"Bearer {twitch_access_token}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        if data["data"]:
            stream_data = data["data"][0]
            return stream_data
        else:
            return None

    @tasks.loop(seconds=5)
    async def stream_status(self):

        for config in self.configurations:
            channel = self.bot.get_channel(config['discord_channel_id'])
            if channel is None:
                print(f"Error: Discord channel with ID {config['discord_channel_id']} not found.")
                continue

            is_live = self.check_stream_status(config['twitch_username'], config['twitch_client_id'], config['twitch_access_token'])

            if is_live:
                title = is_live.get('title', 'No title available')
                category = is_live.get('game_name', 'No category available')
                if config['previous_status'] != 'live':
                    stream_url = f"https://www.twitch.tv/{config['twitch_username']}"
                    embed = discord.Embed(title=f"{config['twitch_username']} is now live!", url=stream_url, color=0x00FF00)
                    embed.add_field(name="Title", value=title, inline=False)
                    embed.add_field(name="Category", value=category, inline=False)
                    embed.set_thumbnail(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{config['twitch_username']}-320x180.jpg")
                    stream_button = StreamButton(stream_url)
                    role_name = ".live"
                    role = discord.utils.get(channel.guild.roles, name=role_name)
                    if role:
                        await channel.send(f"{role.mention}", embed=embed, view=stream_button)
                    else:
                        await channel.send("The .live role does not exist.")



                    config['previous_status'] = 'live'
                    print(f"{config['twitch_username']} is now live!")
                    
            else:
                if config['previous_status'] != 'null':
                    twitch_channel_url = f"https://www.twitch.tv/{config['twitch_username']}"
                    embed = discord.Embed(title=f"{config['twitch_username']} is currently offline", url=twitch_channel_url, color=0xFF0000)
                    await channel.send(embed=embed)
                    config['previous_status'] = 'offline'
                    print(f"{config['twitch_username']} is currently offline")

    @stream_status.before_loop
    async def before_stream_status(self):
        await self.bot.wait_until_ready()


    @commands.command()
    async def ttv(self, ctx, twitch_username: str, channel: discord.TextChannel = None):
        """Add or remove a Twitch user and associate it with a Discord channel"""
        config = next((c for c in self.configurations if c['twitch_username'] == twitch_username), None)

        if channel is None:
            channel = ctx.channel
            if config:
                self.configurations.remove(config)
                self.save_configurations()
                await ctx.send(f"Removed Twitch user {twitch_username} from notifications.")
            else:
                await ctx.send(f"Please specify a channel. Example ',ttv {twitch_username} #general.'")
        else:
            if config and channel.id == config['discord_channel_id']:
                await ctx.send(f"Twitch user {twitch_username} is already configured for notifications on this channel")
            else:
                new_config = {
                    'twitch_username': twitch_username,
                    'discord_channel_id': channel.id,
                    'twitch_client_id': 'gp762nuuoqcoxypju8c569th9wz7q5',  # Replace with your Twitch client ID
                    'twitch_access_token': '3aem92vd1y6x0ad67xlcj731rreyfp',  # Replace with your Twitch OAuth token
                    'previous_status': None
                }
                self.configurations.append(new_config)
                self.save_configurations()
                await ctx.send(f"Added Twitch user {twitch_username} for notifications in {channel.mention}")



    @commands.command()
    async def ttvlist(self, ctx):
        """View the list of Twitch user configurations"""
        if not self.configurations:
            await ctx.send("No Twitch user configurations found.")
            return

        embed = discord.Embed(title="Twitch User Configurations", color=0x00FF00)
        for config in self.configurations:
            channel = self.bot.get_channel(config['discord_channel_id'])
            channel_name = channel.name if channel else "Unknown Channel"
            embed.add_field(name=config['twitch_username'], value=f"Channel: {channel_name} (ID: {config['discord_channel_id']})", inline=False)

        await ctx.send(embed=embed)






async def setup(bot):
    await bot.add_cog(Twitch(bot))