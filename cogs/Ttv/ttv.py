import discord
from discord.ext import commands, tasks
import requests
from discord import ui
import json
import os
import shutil



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

    def check_stream_status(self, twitch_username):
        twitch_client_id = os.getenv('TWITCH_CLIENT_ID')
        twitch_access_token = os.getenv('TWITCH_ACCESS_TOKEN')        
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
            
    @tasks.loop(seconds=45)
    async def stream_status(self):
        for config in self.configurations:
            channel = self.bot.get_channel(config['discord_channel_id'])
            if channel is None:
                print(f"Error: Discord channel with ID {config['discord_channel_id']} not found.")
                continue

            is_live = self.check_stream_status(config['twitch_username'])

            if is_live:
                title = is_live.get('title', 'No title available')
                category = is_live.get('game_name', 'No category available')
                if config['previous_status'] != 'live':
                    stream_url = f"https://www.twitch.tv/{config['twitch_username']}"
                    embed = discord.Embed(title=f"<a:greenalert:1336886706216894524> {config['twitch_username']} is now live!", url=stream_url, color=0x00FF00)
                    embed.add_field(name="Title", value=title, inline=False)
                    embed.add_field(name="Category", value=category, inline=False)
                    embed.set_thumbnail(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{config['twitch_username']}-320x180.jpg")
                    stream_button = StreamButton(stream_url)
                    role_name = ".live"
                    role = discord.utils.get(channel.guild.roles, name=role_name)
                    
                    # Store the message ID for later updates
                    message = await channel.send(f"{role.mention if role else ''}", embed=embed, view=stream_button)
                    config['message_id'] = message.id
                    config['previous_status'] = 'live'
                    print(f"Updated {config['twitch_username']} status to live")
                    self.save_configurations()
                    
            else:
                if config['previous_status'] != 'offline':
                    # Try to fetch the previous message
                    try:
                        if 'message_id' in config:
                            message = await channel.fetch_message(config['message_id'])
                            # Update the existing embed
                            embed = message.embeds[0]
                            embed.color = discord.Color.red()
                            embed.title = f"<a:redalert:1336885681624190979> {config['twitch_username']} is now offline"
                            embed.description = "You missed it! Tune in to see when they go live."
                            
                            # Create new view with disabled red button
                            class OfflineButton(ui.View):
                                def __init__(self):
                                    super().__init__()
                                    self.add_item(ui.Button(
                                        label="Offline",
                                        style=discord.ButtonStyle.danger,
                                        disabled=True
                                    ))
                            
                            await message.edit(embed=embed, view=OfflineButton())
                            config['previous_status'] = 'offline'
                            print(f"Updated {config['twitch_username']} status to offline")
                            self.save_configurations()
                    except (discord.NotFound, discord.HTTPException, AttributeError, KeyError):
                        # If message not found or other error, fallback to sending new message
                        twitch_channel_url = f"https://www.twitch.tv/{config['twitch_username']}"
                        embed = discord.Embed(
                            title=f"{config['twitch_username']} is now offline",
                            url=twitch_channel_url,
                            color=0xFF0000
                        )
                        await channel.send(embed=embed)
                        config['previous_status'] = 'offline'
                        print(f"Updated {config['twitch_username']} status to offline")
                        self.save_configurations()


    @stream_status.before_loop
    async def before_stream_status(self):
        await self.bot.wait_until_ready()

    @commands.command(name='ttvsort')
    @commands.is_owner()  # Only bot owner can use this command
    async def restructure_json(self, ctx):
        try:
            # First, let's back up the existing JSON
            backup_path = '.json/ttv_backup.json'
            shutil.copy('.json/ttv.json', backup_path)
            
            # Read existing data
            with open('.json/ttv.json', 'r') as f:
                old_data = json.load(f)
            
            # Create new structure while preserving existing data
            new_configurations = []
            for config in old_data:
                new_config = {
                    'twitch_username': config.get('twitch_username', ''),
                    'discord_channel_id': config.get('discord_channel_id', 0),
                    'previous_status': config.get('previous_status', 'offline'),
                    'message_id': config.get('message_id', None)
                }
                new_configurations.append(new_config)
            
            # Save the restructured data
            with open('.json/ttv.json', 'w') as f:
                json.dump(new_configurations, f, indent=4)
            
            await ctx.send(f"<:add:1328511998647861390> JSON restructured successfully! Backup saved as {backup_path}")
            
        except Exception as e:
            await ctx.send(f"<:remove:1328511957208268800> Error restructuring JSON: {str(e)}")
            raise e


    @commands.command()
    async def ttv(self, ctx, twitch_username: str, channel: discord.TextChannel = None):
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
                # Only store necessary information in the JSON
                new_config = {
                    'twitch_username': twitch_username,
                    'discord_channel_id': channel.id,
                    'previous_status': 'offline'
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