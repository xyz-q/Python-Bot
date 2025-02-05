from twitchio.ext import commands as twitch_commands
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import asyncio
import json
import os
import random
from dotenv import load_dotenv


class TwitchConfigView(View):
    def __init__(self, cog, page="main"):
        super().__init__(timeout=60)
        self.cog = cog
        self.page = page
        self.setup_buttons()

    def setup_buttons(self):
        if self.page == "main":
            self.add_item(SetChannelButton(self.cog))
            self.add_item(RemoveChannelButton(self.cog))
            self.add_item(SendMessageButton(self.cog))
            self.add_item(TwitchCommandsButton(self.cog))
            self.add_item(SetIntervalButton(self.cog))
        elif self.page == "commands":
            self.add_item(BackToMainButton(self.cog))

class SetChannelButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Set Channel", style=discord.ButtonStyle.green)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetChannelModal(self.cog, interaction.user.id))

class RemoveChannelButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Remove Channel", style=discord.ButtonStyle.red, row=2)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            if user_id in self.cog.config['user_channels']:
                channel = self.cog.config['user_channels'][user_id]
                del self.cog.config['user_channels'][user_id]
                if channel in self.cog.config['channels']:
                    del self.cog.config['channels'][channel]
                self.cog.save_config()
                await self.cog.twitch_bot.close()
                self.cog.setup_twitch_bot()
                await interaction.response.send_message(f"Successfully unlinked Twitch channel: {channel}", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have a Twitch channel linked.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error removing channel: {str(e)}", ephemeral=True)

class SendMessageButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Send Message", style=discord.ButtonStyle.blurple)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in self.cog.config['user_channels']:
            await interaction.response.send_message("You need to link a Twitch channel first!", ephemeral=True)
            return
        await interaction.response.send_modal(SendMessageModal(self.cog, user_id))
class TwitchCommandsButton(discord.ui.Button):
    def __init__(self, cog, row=None):
        super().__init__(label="Twitch Commands", style=discord.ButtonStyle.grey, row=row)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Twitch Bot Commands",
            description="Available commands in Twitch chat:",
            color=discord.Color.purple()
        )
        
        commands_list = []
        for command in self.cog.twitch_bot.commands.values():
            if command.hidden:
                continue
                
            name = f",{command.name}"
            if command.aliases:
                name += f" (aliases: ,{',, ,'.join(command.aliases)})"
                
            description = command.description or "No description available"
            
            if getattr(command, 'mod_only', False):
                description += " (Mods Only)"
                
            commands_list.append(f"{name} - {description}")

        if commands_list:
            embed.add_field(name="Default Commands", value="\n".join(commands_list), inline=False)
        else:
            embed.add_field(name="Default Commands", value="No commands available", inline=False)

        user_id = str(interaction.user.id)
        if user_id in self.cog.config['user_channels']:
            channel = self.cog.config['user_channels'][user_id]
            custom_commands = self.cog.config.get('custom_commands', {}).get(channel, {})
            if custom_commands:
                cmd_list = [f",{cmd} - {response}" for cmd, response in custom_commands.items()]
                embed.add_field(name="Custom Commands", value="\n".join(cmd_list), inline=False)

        view = TwitchConfigView(self.cog, page="commands")
        await interaction.response.edit_message(embed=embed, view=view)


class BackToMainButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Back to Main", style=discord.ButtonStyle.grey)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        embed = await self.cog.create_main_embed(interaction.user)
        view = TwitchConfigView(self.cog, page="main")
        await interaction.response.edit_message(embed=embed, view=view)

class SetIntervalButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Set Interval", style=discord.ButtonStyle.blurple)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if not await self.cog.bot.is_owner(interaction.user):
            await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
            return
        await interaction.response.send_modal(IntervalModal(self.cog))

class SetChannelModal(discord.ui.Modal, title="Set Twitch Channel"):
    channel_name = discord.ui.TextInput(
        label="Twitch Channel Name",
        placeholder="Enter your Twitch channel name",
        required=True,
        max_length=25
    )

    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        channel = self.channel_name.value.lstrip('@').lower()
        try:
            user_id = str(self.user_id)
            if user_id in self.cog.config['user_channels']:
                old_channel = self.cog.config['user_channels'][user_id]
                if old_channel in self.cog.config['channels']:
                    del self.cog.config['channels'][old_channel]

            self.cog.config['user_channels'][user_id] = channel
            self.cog.config['channels'][channel] = {}
            self.cog.save_config()
            await self.cog.twitch_bot.close()
            self.cog.setup_twitch_bot()
            await interaction.response.send_message(f"Successfully linked Twitch channel: {channel}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error setting channel: {str(e)}", ephemeral=True)

class SendMessageModal(discord.ui.Modal, title="Send Twitch Message"):
    message = discord.ui.TextInput(
        label="Message",
        placeholder="Enter the message to send to your Twitch channel",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_name = self.cog.config['user_channels'][self.user_id]
            channel = self.cog.twitch_bot.get_channel(channel_name)
            if channel:
                await channel.send(self.message.value)
                await interaction.response.send_message(f"Message sent to {channel_name}!", ephemeral=True)
            else:
                await interaction.response.send_message("Could not find the channel. Please try again later.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error sending message: {str(e)}", ephemeral=True)

class IntervalModal(discord.ui.Modal, title="Set Auto Message Interval"):
    interval = discord.ui.TextInput(
        label="Interval (seconds)",
        placeholder="Enter interval (minimum 30 seconds)",
        required=True,
        max_length=5
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            seconds = int(self.interval.value)
            if seconds < 30:
                await interaction.response.send_message("Interval must be at least 30 seconds.", ephemeral=True)
                return

            self.cog.config['auto_message_interval'] = seconds
            self.cog.save_config()
            self.cog.auto_message_task.change_interval(seconds=seconds)
            await interaction.response.send_message(f"Auto message interval set to {seconds} seconds", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error setting interval: {str(e)}", ephemeral=True)

class TwitchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_bot = None
        self.auto_messages = {}
        self.last_messages = {}
        self.follow_cache = {}
        self.load_config()
        self.setup_twitch_bot()
        self.auto_message_task.start()


    async def create_main_embed(self, user):
        embed = discord.Embed(
            title="Twitch Bot Configuration",
            description="Use the buttons below to configure your Twitch channel.",
            color=discord.Color.purple()
        )
        
        user_channel = self.config['user_channels'].get(str(user.id), "No channel linked")
        
        embed.add_field(
            name="Your Twitch Channel",
            value=f"Currently linked to: `{user_channel}`",
            inline=False
        )

        if await self.bot.is_owner(user):
            embed.add_field(
                name="Auto Message Interval",
                value=f"Current interval: {self.config['auto_message_interval']}s",
                inline=False
            )

        return embed

    def load_config(self):
        default_config = {
            'channels': {},
            'user_channels': {},
            'auto_messages': {
                'default': [
                    "Don't forget to follow!",
                    "Join our Discord server!",
                    "Stay hydrated!",
                ]
            },
            'follow_messages': [
                "Thanks for the follow, {user}! Welcome to the family!",
                "Hey {user}! Thanks for following!",
                "Welcome aboard, {user}! Thanks for the follow!"
            ],
            'auto_message_interval': 300
        }

        try:
            with open('twitch_config.json', 'r') as f:
                self.config = json.load(f)
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
                self.save_config()
        except FileNotFoundError:
            self.config = default_config
            self.save_config()

    def save_config(self):
        try:
            with open('twitch_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @commands.command(name='twitchconfig', aliases=['twitch', 'twitchbot'])
    async def twitchconfig(self, ctx):
        """Configure Twitch bot settings"""
        try:
            embed = await self.create_main_embed(ctx.author)
            view = TwitchConfigView(self)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            
    def setup_twitch_bot(self):
        class Bot(twitch_commands.Bot):
            def __init__(self, discord_bot, config, parent_cog):
                self.discord_bot = discord_bot
                self.config = config
                self.parent_cog = parent_cog
                
                self.channel_list = [channel.lower() for channel in self.config['channels'].keys()]
                
                super().__init__(
                    token=os.getenv('TWITCH_ACCESS_TOKEN'),
                    client_id=os.getenv('TWITCH_CLIENT_ID'),
                    nick=os.getenv('TWITCH_BOT_NAME'),
                    prefix=',',
                    initial_channels=self.channel_list or ['']
                )
                self.setup_commands()

            def save_config(self):
                with open('config.json', 'w') as f:
                    json.dump(self.config, f, indent=4)

            def load_config(self):
                try:
                    with open('config.json', 'r') as f:
                        self.config = json.load(f)
                except FileNotFoundError:
                    self.config = {}


            def setup_commands(self):
                @self.command(name="help")
                async def help_command(ctx):
                    """Shows all available commands"""
                    commands_list = []
                    
                    # Get default commands
                    for cmd_name, command in ctx.bot.commands.items():
                        if getattr(command, 'hidden', False):
                            continue
                        
                        # Just use the command name without trying to access help/description
                        if cmd_name in ["so", "addcmd", "delcmd"]:  # Mod commands
                            commands_list.append(f",{cmd_name} (Mods Only)")
                        else:
                            commands_list.append(f",{cmd_name}")

                    # Send in chunks
                    await ctx.send("📋 Available Commands:")
                    chunks = [commands_list[i:i + 3] for i in range(0, len(commands_list), 3)]
                    for chunk in chunks:
                        await ctx.send(" | ".join(chunk))

                    # Show custom commands
                    custom_cmds = ctx.bot.config.get('custom_commands', {}).get(ctx.channel.name, {})
                    if custom_cmds:
                        await ctx.send("📋 Custom Commands: " + " | ".join(f"!{cmd}" for cmd in custom_cmds.keys()))


                @self.command(name="setdiscord")
                async def set_discord_link(self, ctx: twitch_commands.Context, *, link: str = None):
                    """Set the Discord invite link (Mods Only)"""
                    print(f"Command received from channel: {ctx.channel.name}")
                    print(f"Command sent by: {ctx.author.name}")
                    
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        print(f"Permission check failed - User: {ctx.author.name}, Mod: {ctx.author.is_mod}, Channel: {ctx.channel.name}")
                        return

                    # Get the message parts
                    try:
                        # Try to get the actual Discord link from the input
                        if not link or link.isspace() or ord(link[0]) > 126:  # Check for invalid characters
                            await ctx.send("Usage: !setdiscord https://discord.gg/invite")
                            return
                            
                        # Clean the link more aggressively
                        cleaned_link = ''
                        for char in link:
                            if 32 <= ord(char) <= 126:  # Only allow standard ASCII printable characters
                                cleaned_link += char
                                
                        cleaned_link = cleaned_link.strip()
                        print(f"Cleaned link: {repr(cleaned_link)}")
                        
                        if not cleaned_link:
                            await ctx.send("Usage: !setdiscord https://discord.gg/invite")
                            return

                        # Basic Discord invite link validation
                        if not (cleaned_link.startswith('https://discord.gg/') or cleaned_link.startswith('discord.gg/')):
                            print(f"Link validation failed: {cleaned_link}")
                            await ctx.send("❌ Please provide a valid Discord invite link (e.g., https://discord.gg/invite)")
                            return

                        try:
                            with open('discord_links.json', 'r') as f:
                                discord_links = json.load(f)
                                print(f"Current discord_links.json content: {discord_links}")
                        except (FileNotFoundError, json.JSONDecodeError):
                            print("No existing discord_links.json found or file is empty")
                            discord_links = {}

                        discord_links[ctx.channel.name] = cleaned_link
                        print(f"Updated discord_links dictionary: {discord_links}")
                        
                        with open('discord_links.json', 'w') as f:
                            json.dump(discord_links, f, indent=4)
                            print("Successfully wrote to discord_links.json")
                            
                        await ctx.send(f"✅ Discord invite link set to: {cleaned_link}")
                        
                    except Exception as e:
                        print(f"Error processing command: {e}")
                        await ctx.send("❌ Error processing command. Please try again with a valid Discord invite link.")



                @self.command(name="discord")
                async def discord_command(self, ctx: twitch_commands.Context):
                    """Get the Discord server link"""
                    print(f"Discord command received from channel: {ctx.channel.name}")
                    
                    try:
                        with open('discord_links.json', 'r') as f:
                            discord_links = json.load(f)
                            print(f"Current discord_links.json content: {discord_links}")
                            link = discord_links.get(ctx.channel.name, 'No Discord link set')
                            print(f"Found link for channel: {link}")
                    except (FileNotFoundError, json.JSONDecodeError):
                        print("No discord_links.json found or file is empty")
                        link = 'No Discord link set'
                    
                    if link != 'No Discord link set':
                        await ctx.send(f"Join our Discord server! {link}")
                    else:
                        await ctx.send(link)




                @self.command(name="lurk")
                async def lurk_command(ctx: twitch_commands.Context):
                    """Let everyone know you're lurking"""
                    await ctx.send(f"Thanks for lurking, {ctx.author.name}! Enjoy your stay 👀")

                @self.command(name="socials")
                async def socials_command(ctx: twitch_commands.Context):
                    """Display social media links"""
                    if ctx.channel.name in self.config.get('social_links', {}):
                        await ctx.send(f"Follow {ctx.channel.name} on: {self.config['social_links'][ctx.channel.name]}")
                    else:
                        await ctx.send("No social links set for this channel!")

                @self.command(name="so")
                async def shoutout_command(ctx: twitch_commands.Context, target: str = None):
                    """Give a shoutout to another streamer (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return
                    
                    if not target:
                        await ctx.send("Please specify a user to shoutout!")
                        return
                        
                    target = target.lstrip('@')
                    await ctx.send(f"Go check out @{target} at twitch.tv/{target} ! They're awesome!")

                @self.command(name="addcmd")
                async def add_command(ctx: twitch_commands.Context, cmd_name: str = None, *, response: str = None):
                    """Add a custom command (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return

                    if not cmd_name or not response:
                        await ctx.send("Usage: ,addcmd <command_name> <response>")
                        return

                    cmd_name = cmd_name.lower()
                    if cmd_name in self.commands:
                        await ctx.send(f"Cannot override default command: ,{cmd_name}")
                        return

                    if 'custom_commands' not in self.config:
                        self.config['custom_commands'] = {}
                    
                    if ctx.channel.name not in self.config['custom_commands']:
                        self.config['custom_commands'][ctx.channel.name] = {}

                    self.config['custom_commands'][ctx.channel.name][cmd_name] = response
                    self.parent_cog.save_config()
                    await ctx.send(f"Command ,{cmd_name} has been added!")

                @self.command(name="delcmd")
                async def delete_command(ctx: twitch_commands.Context, cmd_name: str = None):
                    """Delete a custom command (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return

                    if not cmd_name:
                        await ctx.send("Usage: ,delcmd <command_name>")
                        return

                    cmd_name = cmd_name.lower()
                    if cmd_name in self.commands:
                        await ctx.send(f"Cannot delete default command: ,{cmd_name}")
                        return

                    if (self.config.get('custom_commands', {}).get(ctx.channel.name, {}).get(cmd_name)):
                        del self.config['custom_commands'][ctx.channel.name][cmd_name]
                        self.parent_cog.save_config()
                        await ctx.send(f"Command ,{cmd_name} has been deleted!")
                    else:
                        await ctx.send(f"Command ,{cmd_name} not found!")

            async def event_ready(self):
                print(f'Logged into Twitch | {self.nick}')
                print(f"Monitoring channels: {self.channel_list}")

            async def event_message(self, message):
                if message.echo:
                    return

                # Handle custom commands first
                if message.content.startswith(','):
                    cmd = message.content[1:].split()[0].lower()
                    if (self.config.get('custom_commands', {}).get(message.channel.name, {}).get(cmd)):
                        await message.channel.send(self.config['custom_commands'][message.channel.name][cmd])
                        return

                # Handle built-in commands
                await self.handle_commands(message)

        self.twitch_bot = Bot(self.bot, self.config, self)
        self.bot.loop.create_task(self.twitch_bot.start())




    @tasks.loop(seconds=30)
    async def auto_message_task(self):
        if not hasattr(self, 'config'):
            return
            
        for channel_name in self.config.get('channels', {}).keys():
            channel = self.twitch_bot.get_channel(channel_name)
            if channel:
                stream = await self.twitch_bot.fetch_streams(user_logins=[channel_name])
                if stream:
                    messages = self.auto_messages.get(
                        channel_name, 
                        self.config['auto_messages']['default']
                    )
                    if messages:
                        message = random.choice(messages)
                        if self.last_messages.get(channel_name) != message:
                            await channel.send(message)
                            self.last_messages[channel_name] = message

async def setup(bot):
    await bot.add_cog(TwitchCog(bot))
