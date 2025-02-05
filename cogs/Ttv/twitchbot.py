from twitchio.ext import commands as twitch_commands
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import asyncio
import json
import os
import random
from dotenv import load_dotenv
import asyncio


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
        try:
            embed = discord.Embed(
                title="Twitch Bot Commands",
                description="Available commands in Twitch chat:",
                color=discord.Color.purple()
            )
            
            commands_list = []
            
            # Debug print
            
            
            # Get commands from the bot instance
            for cmd_name in self.cog.twitch_bot.commands:
                name = f",{cmd_name}"
                
                # Add to commands list with basic description
                if cmd_name in ["so", "addcmd", "delcmd", "setdiscord"]:
                    commands_list.append(f"{name} (Mods Only)")
                else:
                    commands_list.append(name)

            if commands_list:
                embed.add_field(
                    name="Default Commands", 
                    value="\n".join(sorted(commands_list)), 
                    inline=False
                )
            else:
                embed.add_field(
                    name="Default Commands", 
                    value="No commands available", 
                    inline=False
                )

            # Custom commands
            user_id = str(interaction.user.id)
            if user_id in self.cog.config['user_channels']:
                channel = self.cog.config['user_channels'][user_id]
                custom_commands = self.cog.config.get('custom_commands', {}).get(channel, {})
                if custom_commands:
                    cmd_list = [f",{cmd} - {response}" for cmd, response in custom_commands.items()]
                    embed.add_field(
                        name="Custom Commands", 
                        value="\n".join(sorted(cmd_list)), 
                        inline=False
                    )

            view = TwitchConfigView(self.cog, page="commands")
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"Error in TwitchCommandsButton callback: {str(e)}")
            try:
                error_embed = discord.Embed(
                    title="Error",
                    description="An error occurred while fetching commands.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=error_embed)
            except:
                pass




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
        super().__init__(label="Set Interval", style=discord.ButtonStyle.blurple, row=2)
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
            with open('.json/twitch_config.json', 'r') as f:
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
            with open('.json/twitch_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @commands.command(name='twitchconfig', aliases=['twitch', 'twitchbot'])
    async def twitchconfig(self, ctx):
        await ctx.message.delete()
        """Configure Twitch bot settings"""
        try:
            embed = await self.create_main_embed(ctx.author)
            view = TwitchConfigView(self)
            twitchembed = await ctx.send(embed=embed, view=view)
            await asyncio.sleep(180)
            await twitchembed.delete()
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



            def setup_commands(self):
                @self.command(name="help")
                async def help_command(ctx):
                    """Shows all available commands"""
                    commands_list = []
                    
                    # Get default commands
                    for cmd_name, command in ctx.bot.commands.items():
                        if getattr(command, 'hidden', False):
                            continue
                        
                        if cmd_name in ["so", "addcmd", "delcmd"]:  # Mod commands
                            commands_list.append(f",{cmd_name} (Mods Only)")
                        else:
                            commands_list.append(f",{cmd_name}")

                    # Send in chunks
                    await ctx.send(f"@{ctx.author.name} 📋 Available Commands:")
                    chunks = [commands_list[i:i + 3] for i in range(0, len(commands_list), 3)]
                    for chunk in chunks:
                        await ctx.send("| ".join(chunk))

                    # Show custom commands
                    custom_cmds = ctx.bot.config.get('custom_commands', {}).get(ctx.channel.name, {})
                    if custom_cmds:
                        await ctx.send(f"@{ctx.author.name} 📋 Custom Commands: " + " | ".join(f",{cmd}" for cmd in custom_cmds.keys()))

                @self.command(name="setdiscord")
                async def set_discord_link(ctx, *, content: str):
                    """Set the Discord invite link (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return

                    if not content:
                        await ctx.send(f"@{ctx.author.name} Usage: ,setdiscord <discord invite link>")
                        return

                    if "discord.gg" not in content and "discord.com" not in content:
                        await ctx.send(f"@{ctx.author.name} ❌ Please provide a valid Discord invite link")
                        return

                    try:
                        with open('.json/discord_links.json', 'r') as f:
                            discord_links = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        discord_links = {}

                    discord_links[ctx.channel.name] = content
                    
                    try:
                        with open('.json/discord_links.json', 'w') as f:
                            json.dump(discord_links, f, indent=4)
                    except Exception as e:
                        print(f"Error writing to file: {e}")
                        return
                        
                    await ctx.send(f"@{ctx.author.name} ✅ Discord invite link set!")

                @self.command(name="discord")
                async def discord_command(ctx):
                    """Display the Discord invite link"""
                    try:
                        with open('.json/discord_links.json', 'r') as f:
                            discord_links = json.load(f)
                            
                        channel_name = ctx.channel.name
                        if channel_name in discord_links:
                            await ctx.send(f"@{ctx.author.name} Join our Discord! {discord_links[channel_name]}")
                        else:
                            await ctx.send(f"@{ctx.author.name} No Discord link has been set for this channel!")
                            
                    except (FileNotFoundError, json.JSONDecodeError):
                        await ctx.send(f"@{ctx.author.name} No Discord link has been set for this channel!")
                    except Exception as e:
                        print(f"Error: {e}")
                        await ctx.send(f"@{ctx.author.name} Error retrieving Discord link!")

                @self.command(name="lurk")
                async def lurk_command(ctx):
                    """Let everyone know you're lurking"""
                    await ctx.send(f"Thanks for lurking, @{ctx.author.name}! Enjoy your stay 👀")

                @self.command(name="socials")
                async def socials_command(ctx):
                    """Display social media links"""
                    if ctx.channel.name in ctx.bot.config.get('social_links', {}):
                        await ctx.send(f"@{ctx.author.name} Follow {ctx.channel.name} on: {ctx.bot.config['social_links'][ctx.channel.name]}")
                    else:
                        await ctx.send(f"@{ctx.author.name} No social links set for this channel!")

                @self.command(name="so")
                async def shoutout_command(ctx, target: str = None):
                    """Give a shoutout to another streamer (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return
                    
                    if not target:
                        await ctx.send(f"@{ctx.author.name} Please specify a user to shoutout!")
                        return
                        
                    target = target.lstrip('@')
                    await ctx.send(f"@{ctx.author.name} gives a shoutout to @{target}! Go check them out at twitch.tv/{target} ! They're awesome!")

                @self.command(name="addcmd")
                async def add_command(ctx, cmd_name: str = None, *, response: str = None):
                    """Add a custom command (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return

                    if not cmd_name or not response:
                        await ctx.send(f"@{ctx.author.name} Usage: ,addcmd <command_name> <response>")
                        return

                    cmd_name = cmd_name.lower()
                    if cmd_name in ctx.bot.commands:
                        await ctx.send(f"@{ctx.author.name} Cannot override default command: ,{cmd_name}")
                        return

                    if 'custom_commands' not in ctx.bot.config:
                        ctx.bot.config['custom_commands'] = {}
                    
                    if ctx.channel.name not in ctx.bot.config['custom_commands']:
                        ctx.bot.config['custom_commands'][ctx.channel.name] = {}

                    ctx.bot.config['custom_commands'][ctx.channel.name][cmd_name] = response
                    ctx.bot.parent_cog.save_config()
                    await ctx.send(f"@{ctx.author.name} Command ,{cmd_name} has been added!")

                @self.command(name="delcmd")
                async def delete_command(ctx, cmd_name: str = None):
                    """Delete a custom command (Mods Only)"""
                    if not (ctx.author.is_mod or ctx.author.name == ctx.channel.name):
                        return

                    if not cmd_name:
                        await ctx.send(f"@{ctx.author.name} Usage: ,delcmd <command_name>")
                        return

                    cmd_name = cmd_name.lower()
                    if cmd_name in ctx.bot.commands:
                        await ctx.send(f"@{ctx.author.name} Cannot delete default command: ,{cmd_name}")
                        return

                    if (ctx.bot.config.get('custom_commands', {}).get(ctx.channel.name, {}).get(cmd_name)):
                        del ctx.bot.config['custom_commands'][ctx.channel.name][cmd_name]
                        ctx.bot.parent_cog.save_config()
                        await ctx.send(f"@{ctx.author.name} Command ,{cmd_name} has been deleted!")
                    else:
                        await ctx.send(f"@{ctx.author.name} Command ,{cmd_name} not found!")

            async def event_ready(self):
                await asyncio.sleep(10)
                print(f'Logged into Twitch | {self.nick}')


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
