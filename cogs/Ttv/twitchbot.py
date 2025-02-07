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
import time


class TwitchConfigView(View):
    def __init__(self, cog, page="main"):
        super().__init__(timeout=180)
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
            self.add_item(AutoMessagesButton(self.cog)) 
            self.add_item(CloseButton(self.cog))           
            
        elif self.page == "commands":
            self.add_item(AddCommandButton(self.cog))
            self.add_item(DeleteCommandButton(self.cog))
            self.add_item(CloseButton(self.cog))
            
            self.add_item(BackToMainButton(self.cog))
        elif self.page == "auto_messages":
            self.add_item(AddAutoMessageButton(self.cog))
            self.add_item(RemoveAutoMessageButton(self.cog))
            self.add_item(FollowMessageButton(self.cog))
            self.add_item(BackToMainButton(self.cog))    
            self.add_item(CloseButton(self.cog))        


class CloseButton(discord.ui.Button):
    def __init__(self, cog):  # Add cog parameter
        super().__init__(
            label="",
            style=discord.ButtonStyle.red,
            emoji="✖️",
            row=4
        )
        self.cog = cog  # Store the cog reference

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()


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
                
                # Update the embed after removing the channel
                new_embed = await self.cog.create_main_embed(interaction.user)
                await interaction.message.edit(embed=new_embed)
                
                await interaction.response.send_message(f"Successfully unlinked Twitch channel: {channel}", ephemeral=True, delete_after=8)
            else:
                await interaction.response.send_message("You don't have a Twitch channel linked.", ephemeral=True, delete_after=8)
        except Exception as e:
            await interaction.response.send_message(f"Error removing channel: {str(e)}", ephemeral=True, delete_after=8)


class SendMessageButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Send Message", style=discord.ButtonStyle.blurple)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in self.cog.config['user_channels']:
            await interaction.response.send_message("You need to link a Twitch channel first!", ephemeral=True, delete_after=8)
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
            await asyncio.sleep(120)
            new_embed = await self.cog.create_main_embed(interaction.user)
            await interaction.message.edit(embed=new_embed, view=TwitchConfigView(self.cog))            
            
        except Exception as e:
            try:
                error_embed = discord.Embed(
                    title="Error",
                    description="An error occurred while fetching commands.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=error_embed)
            except:
                pass

class AddCommandModal(discord.ui.Modal, title="Add Custom Command"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        
        self.cmd_name = discord.ui.TextInput(
            label="Command Name",
            placeholder="Enter command name without prefix",
            min_length=1,
            max_length=20,
            required=True
        )
        self.response = discord.ui.TextInput(
            label="Command Response",
            placeholder="What should the bot say when command is used?",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.cmd_name)
        self.add_item(self.response)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            if user_id not in self.cog.config['user_channels']:
                await interaction.response.send_message("You need to set up your Twitch channel first!", ephemeral=True)
                return

            channel = self.cog.config['user_channels'][user_id]
            cmd_name = self.cmd_name.value.lower()
            response = self.response.value

            if cmd_name in self.cog.twitch_bot.commands:
                await interaction.response.send_message(f"Cannot override default command: ,{cmd_name}", ephemeral=True)
                return

            if 'custom_commands' not in self.cog.config:
                self.cog.config['custom_commands'] = {}
            
            if channel not in self.cog.config['custom_commands']:
                self.cog.config['custom_commands'][channel] = {}

            self.cog.config['custom_commands'][channel][cmd_name] = response
            self.cog.save_config()

            # Trigger the TwitchCommandsButton callback to refresh the view
            await TwitchCommandsButton(self.cog).callback(interaction)
            
        except Exception as e:
            print(f"Error in AddCommandModal on_submit: {str(e)}")
            await interaction.response.send_message("An error occurred", ephemeral=True)


class DeleteCommandModal(discord.ui.Modal, title="Delete Custom Command"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        
        self.cmd_name = discord.ui.TextInput(
            label="Command Name",
            placeholder="Enter command name to delete",
            min_length=1,
            max_length=20,
            required=True
        )
        self.add_item(self.cmd_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            if user_id not in self.cog.config['user_channels']:
                await interaction.response.send_message("You need to set up your Twitch channel first!", ephemeral=True)
                return

            channel = self.cog.config['user_channels'][user_id]
            cmd_name = self.cmd_name.value.lower()

            if cmd_name in self.cog.twitch_bot.commands:
                await interaction.response.send_message(f"Cannot delete default command: ,{cmd_name}", ephemeral=True)
                return

            if (self.cog.config.get('custom_commands', {}).get(channel, {}).get(cmd_name)):
                del self.cog.config['custom_commands'][channel][cmd_name]
                self.cog.save_config()
                
                # Trigger the TwitchCommandsButton callback to refresh the view
                await TwitchCommandsButton(self.cog).callback(interaction)
            else:
                await interaction.response.send_message(f"Command ,{cmd_name} not found!", ephemeral=True)

        except Exception as e:
            print(f"Error in DeleteCommandModal on_submit: {str(e)}")
            await interaction.response.send_message("An error occurred", ephemeral=True)


class AddCommandButton(discord.ui.Button):
    def __init__(self, cog, row=None):
        super().__init__(label="Add Command", style=discord.ButtonStyle.green, row=row)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        # Check if user is mod or channel owner
        user_id = str(interaction.user.id)
        if user_id not in self.cog.config['user_channels']:
            await interaction.response.send_message("You need to set up your Twitch channel first!", ephemeral=True)
            return
            
        modal = AddCommandModal(self.cog)
        await interaction.response.send_modal(modal)

class DeleteCommandButton(discord.ui.Button):
    def __init__(self, cog, row=None):
        super().__init__(label="Delete Command", style=discord.ButtonStyle.red, row=row)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        # Check if user is mod or channel owner
        user_id = str(interaction.user.id)
        if user_id not in self.cog.config['user_channels']:
            await interaction.response.send_message("You need to set up your Twitch channel first!", ephemeral=True)
            return
            
        modal = DeleteCommandModal(self.cog)
        await interaction.response.send_modal(modal)


class BackToMainButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Back to Main", style=discord.ButtonStyle.grey, row=2)
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
            await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True, delete_after=8)
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
            
            # Handle channel changes
            if user_id in self.cog.config['user_channels']:
                old_channel = self.cog.config['user_channels'][user_id]
                if old_channel in self.cog.config['channels']:
                    del self.cog.config['channels'][old_channel]
                    # Part the old channel
                    await self.cog.twitch_bot.part_channels([old_channel])

            # Update configuration
            self.cog.config['user_channels'][user_id] = channel
            self.cog.config['channels'][channel] = {}
            self.cog.save_config()

            # Join the new channel
            await self.cog.twitch_bot.join_channels([channel])
            
            # Update the embed
            new_embed = await self.cog.create_main_embed(interaction.user)
            await interaction.message.edit(embed=new_embed)
            
            await interaction.response.send_message(f"Successfully linked Twitch channel: {channel}", ephemeral=True, delete_after=8)
            
        except Exception as e:
            await interaction.response.send_message(f"Error setting channel: {str(e)}", ephemeral=True, delete_after=8)


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
                await interaction.response.send_message(f"Message sent to {channel_name}!", ephemeral=True, delete_after=8)
            else:
                await interaction.response.send_message("Could not find the channel. Please try again later.", ephemeral=True, delete_after=8)
        except Exception as e:
            await interaction.response.send_message(f"Error sending message: {str(e)}", ephemeral=True, delete_after=8)

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
                await interaction.response.send_message("Interval must be at least 30 seconds.", ephemeral=True, delete_after=8)
                return

            self.cog.config['auto_message_interval'] = seconds
            self.cog.save_config()
            self.cog.auto_message_task.change_interval(seconds=seconds)
            
            # Update the embed after changing the interval
            new_embed = await self.cog.create_main_embed(interaction.user)
            await interaction.message.edit(embed=new_embed)
            
            await interaction.response.send_message(f"Auto message interval set to {seconds} seconds", ephemeral=True, delete_after=8)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True, delete_after=8)
        except Exception as e:
            await interaction.response.send_message(f"Error setting interval: {str(e)}", ephemeral=True, delete_after=8)


class AutoMessagesButton(discord.ui.Button):
    def __init__(self, cog, row=None):
        super().__init__(label="Auto Messages", style=discord.ButtonStyle.grey, row=2)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        try:

            
            embed = discord.Embed(
                title="Auto Messages Configuration",
                description="Manage your automatic messages here",
                color=discord.Color.purple()
            )
            
            user_id = str(interaction.user.id)
            if user_id in self.cog.config['user_channels']:
                channel = self.cog.config['user_channels'][user_id]

                
                # Simpler approach - directly access the list if it exists
                if 'auto_messages' in self.cog.config and channel in self.cog.config['auto_messages']:
                    channel_messages = self.cog.config['auto_messages'][channel]
                    
                    if channel_messages:
                        messages_list = []
                        for i, msg in enumerate(channel_messages, 1):
                            messages_list.append(f"Message {i}: {msg}")
                        
                        embed.add_field(
                            name="Auto Messages", 
                            value="\n".join(messages_list), 
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="Auto Messages",
                            value="No auto messages set up yet.",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="Auto Messages",
                        value="No auto messages set up yet.",
                        inline=False
                    )

                # Similar direct approach for follow message
                if 'follow_messages' in self.cog.config and channel in self.cog.config['follow_messages']:
                    follow_message = self.cog.config['follow_messages'][channel]
                else:
                    follow_message = "No follow message set"
                    
                embed.add_field(
                    name="Follow Message",
                    value=follow_message,
                    inline=False
                )

            view = TwitchConfigView(self.cog, page="auto_messages")
            await interaction.response.edit_message(embed=embed, view=view)
            await asyncio.sleep(120)
            new_embed = await self.cog.create_main_embed(interaction.user)
            await interaction.message.edit(embed=new_embed, view=TwitchConfigView(self.cog))             
            
        except Exception as e:
            try:
                error_embed = discord.Embed(
                    title="Error",
                    description="An error occurred while fetching auto messages.",
                    color=discord.Color.red()
                )
                await interaction.response.edit_message(embed=error_embed)
            except:
                pass




# Individual buttons for the Auto Messages View
class ListAutoMessagesButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(
            label="List Messages",
            style=discord.ButtonStyle.primary,
            emoji="📋"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        user_channel = self.cog.config['user_channels'].get(str(interaction.user.id))
        auto_messages = self.cog.config.get('auto_messages', {}).get(user_channel, [])
        
        embed = discord.Embed(
            title="Auto Messages List",
            color=discord.Color.blue()
        )
        
        if auto_messages:
            for i, msg in enumerate(auto_messages, 1):
                embed.add_field(
                    name=f"Message {i}",
                    value=msg,
                    inline=False
                )
        else:
            embed.description = "No auto messages configured."
            
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=8)

class AddAutoMessageButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(
            label="Add Message",
            style=discord.ButtonStyle.green,
            emoji="➕"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddAutoMessageModal(self.cog))

class AddAutoMessageModal(discord.ui.Modal, title="Add Auto Message"):
    message = discord.ui.TextInput(
        label="Message Content",
        placeholder="Enter your auto message here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            if user_id not in self.cog.config['user_channels']:
                await interaction.response.send_message("You need to set a channel first!", ephemeral=True, delete_after=8)
                return

            channel = self.cog.config['user_channels'][user_id]
            
            # Initialize auto_messages if it doesn't exist
            if not isinstance(self.cog.config.get('auto_messages', {}), dict):
                self.cog.config['auto_messages'] = {}
            if channel not in self.cog.config['auto_messages']:
                self.cog.config['auto_messages'][channel] = []

            # Add the new message
            self.cog.config['auto_messages'][channel].append(self.message.value)
            self.cog.save_config()

            # Update the embed
            embed = discord.Embed(
                title="Auto Messages Configuration",
                description="Manage your automatic messages here",
                color=discord.Color.purple()
            )

            # Show auto messages
            messages = self.cog.config['auto_messages'][channel]
            if messages:
                messages_list = []
                for i, msg in enumerate(messages, 1):
                    messages_list.append(f"Message {i}: {msg}")
                embed.add_field(
                    name="Auto Messages",
                    value="\n".join(messages_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Auto Messages",
                    value="No auto messages set up yet.",
                    inline=False
                )

            # Show follow message
            if isinstance(self.cog.config.get('follow_messages', {}), dict):
                follow_message = self.cog.config['follow_messages'].get(channel, "No follow message set")
            else:
                follow_message = "No follow message set"
                
            embed.add_field(
                name="Follow Message",
                value=follow_message,
                inline=False
            )

            view = TwitchConfigView(self.cog, page="auto_messages")
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.send_message("Auto message added successfully!", ephemeral=True, delete_after=8)
            
        except Exception as e:
            print(f"Error in AddAutoMessageModal: {str(e)}")
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True, delete_after=8)
class RemoveAutoMessageButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(
            label="Remove Message",
            style=discord.ButtonStyle.red,
            emoji="🗑️"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            print(f"User ID: {user_id}")  # Debug print
            
            if user_id not in self.cog.config['user_channels']:
                await interaction.response.send_message("You need to set a channel first!", ephemeral=True, delete_after=8)
                return

            channel = self.cog.config['user_channels'][user_id]
  # Debug print
            
            if not isinstance(self.cog.config.get('auto_messages', {}), dict):
                print("auto_messages is not a dictionary")  # Debug print
                await interaction.response.send_message("No auto messages found.", ephemeral=True, delete_after=8)
                return

            messages = self.cog.config['auto_messages'].get(channel, [])
            print(f"Messages found: {messages}")  # Debug print

            if not messages:
                await interaction.response.send_message("No messages to remove!", ephemeral=True, delete_after=8)
                return

            # Create select menu for message removal
            options = [
                discord.SelectOption(
                    label=f"Message {i+1}",
                    description=msg[:50] + "..." if len(msg) > 50 else msg,
                    value=str(i)
                ) for i, msg in enumerate(messages)
            ]

            select = discord.ui.Select(
                placeholder="Choose a message to remove...",
                options=options,
                min_values=1,
                max_values=1
            )

            async def select_callback(select_interaction):
                try:
                    index = int(select_interaction.data['values'][0])
                    removed_message = messages.pop(index)
                    print(f"Removed message: {removed_message}")  # Debug print
                    
                    self.cog.config['auto_messages'][channel] = messages
                    self.cog.save_config()
                    print(f"Updated config: {self.cog.config}")  # Debug print

                    # Update embed
                    embed = discord.Embed(
                        title="Auto Messages Configuration",
                        description="Manage your automatic messages here",
                        color=discord.Color.purple()
                    )

                    if messages:
                        messages_list = []
                        for i, msg in enumerate(messages, 1):
                            messages_list.append(f"Message {i}: {msg}")
                        embed.add_field(
                            name="Auto Messages",
                            value="\n".join(messages_list),
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="Auto Messages",
                            value="No auto messages set up yet.",
                            inline=False
                        )

                    # Show follow message
                    if isinstance(self.cog.config.get('follow_messages', {}), dict):
                        follow_message = self.cog.config['follow_messages'].get(channel, "No follow message set")
                    else:
                        follow_message = "No follow message set"
                    
                    embed.add_field(
                        name="Follow Message",
                        value=follow_message,
                        inline=False
                    )

                    view = TwitchConfigView(self.cog, page="auto_messages")
                    await interaction.message.edit(embed=embed, view=view)
                    await select_interaction.response.send_message(f"Message removed successfully!", ephemeral=True, delete_after=8)
                
                except Exception as e:
                    print(f"Error in select callback: {str(e)}")  # Debug print
                    await select_interaction.response.send_message(f"Error removing message: {str(e)}", ephemeral=True, delete_after=8)

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)
            await interaction.response.send_message("Select a message to remove:", view=view, ephemeral=True, delete_after=8)

        except Exception as e:
            print(f"Error in RemoveAutoMessageButton: {str(e)}")  # Debug print
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True, delete_after=8)


class RemoveAutoMessageModal(discord.ui.Modal, title="Remove Auto Message"):
    message_number = discord.ui.TextInput(
        label="Message Number",
        placeholder="Enter the message number to remove",
        required=True,
        max_length=3
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            msg_num = int(self.message_number.value)
            user_channel = self.cog.config['user_channels'].get(str(interaction.user.id))
            messages = self.cog.config.get('auto_messages', {}).get(user_channel, [])
            
            if 0 < msg_num <= len(messages):
                removed_msg = messages.pop(msg_num - 1)
                self.cog.config['auto_messages'][user_channel] = messages
                self.cog.save_config()

                # Create updated embed
                embed = discord.Embed(
                    title="Auto Messages Configuration",
                    description="Manage your automatic messages here",
                    color=discord.Color.blue()
                )
                
                for i, msg in enumerate(messages, 1):
                    embed.add_field(
                        name=f"Message {i}",
                        value=msg,
                        inline=False
                    )
                if not messages:
                    embed.add_field(
                        name="No Messages",
                        value="You haven't set up any auto messages yet.",
                        inline=False
                    )

                follow_message = self.cog.config.get('follow_messages', {}).get(user_channel, "No follow message set")
                embed.add_field(
                    name="Follow Message",
                    value=follow_message,
                    inline=False
                )

                await interaction.message.edit(embed=embed)
                await interaction.response.send_message(f"Removed message: {removed_msg}", ephemeral=True, delete_after=8)
            else:
                await interaction.response.send_message("Invalid message number!", ephemeral=True, delete_after=8)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True, delete_after=8)

class FollowMessageButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(
            label="Follow Message",
            style=discord.ButtonStyle.secondary,
            emoji="🎯",
            row=2
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FollowMessageModal(self.cog))

class FollowMessageModal(discord.ui.Modal, title="Set Follow Message"):
    message = discord.ui.TextInput(
        label="Follow Message",
        placeholder="Enter message (use {user} for follower's name)",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            if user_id not in self.cog.config['user_channels']:
                await interaction.response.send_message("You need to set a channel first!", ephemeral=True, delete_after=8)
                return

            channel = self.cog.config['user_channels'][user_id]

            # Initialize follow_messages if it doesn't exist or isn't a dict
            if not isinstance(self.cog.config.get('follow_messages', {}), dict):
                self.cog.config['follow_messages'] = {}

            # Set the follow message
            self.cog.config['follow_messages'][channel] = self.message.value
            self.cog.save_config()

            # Update the embed
            embed = discord.Embed(
                title="Auto Messages Configuration",
                description="Manage your automatic messages here",
                color=discord.Color.purple()
            )

            # Show auto messages
            if isinstance(self.cog.config.get('auto_messages', {}), dict):
                messages = self.cog.config['auto_messages'].get(channel, [])
                if messages:
                    messages_list = []
                    for i, msg in enumerate(messages, 1):
                        messages_list.append(f"Message {i}: {msg}")
                    embed.add_field(
                        name="Auto Messages",
                        value="\n".join(messages_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Auto Messages",
                        value="No auto messages set up yet.",
                        inline=False
                    )

            # Show follow message
            embed.add_field(
                name="Follow Message",
                value=self.message.value,
                inline=False
            )

            view = TwitchConfigView(self.cog, page="auto_messages")
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.send_message("Follow message set successfully!", ephemeral=True, delete_after=8)
            
        except Exception as e:
            print(f"Error in FollowMessageModal: {str(e)}")
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True, delete_after=8)
            
class HomeButton(discord.ui.Button):
    def __init__(self, cog, original_message):
        super().__init__(
            label="Home",
            style=discord.ButtonStyle.secondary,
            emoji="🏠"
        )
        self.cog = cog
        self.original_message = original_message

    async def callback(self, interaction: discord.Interaction):
        embed = await self.cog.create_main_embed(interaction.user)
        view = TwitchConfigView(self.cog)
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.defer()






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
        self.channel_last_message = {}


    async def create_main_embed(self, user):
        embed = discord.Embed(
            title="Twitch Bot Configuration",
            description="Use the buttons below to configure your Twitch channel.",
            color=discord.Color.purple()
        )
        
        user_channel = self.config['user_channels'].get(str(user.id), "No channel linked")
        
        
    # Check if channel is live
        if user_channel != "No channel linked":
            try:
                # Debug print to see what's happening

                
                # Fetch stream info
                streams = await self.twitch_bot.fetch_streams(user_logins=[user_channel])

                
                is_live = bool(streams)
                status = "<a:greenalert:1336886706216894524> Live" if is_live else "<a:redalert:1336885681624190979> Offline"
                
                if is_live and streams:
                    stream_info = streams[0]
                    embed.add_field(
                        name="Stream Status",
                        value=f"{status}\n"
                            f"Title: {stream_info.title}\n"
                            f"Game: {stream_info.game_name}\n"
                            f"Viewers: {stream_info.viewer_count}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Stream Status",
                        value=status,
                        inline=False
                    )
            except Exception as e:
                print(f"Error fetching stream status: {e}")
                embed.add_field(
                    name="Stream Status",
                    value="<:WARNING:1336887375158181899> Unable to fetch status",
                    inline=False
                )

        
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
            
            # Auto refresh status every 60 seconds
            for _ in range(1):  # Will refresh 3 times (3 minutes total)
                await asyncio.sleep(180)
                try:
                    new_embed = await self.create_main_embed(ctx.author)
                    await twitchembed.edit(embed=new_embed)
                except discord.NotFound:
                    break  # Message was deleted
                except Exception as e:
                    print(f"Error refreshing embed: {e}")
                    
            await twitchembed.delete()
        except Exception as e:
            print(f"Twitch message deleted.")

    def setup_twitch_bot(self):
        class Bot(twitch_commands.Bot):
            def __init__(self, discord_bot, config, parent_cog):
                self.discord_bot = discord_bot
                self.config = config
                self.parent_cog = parent_cog
                self.channel_last_message = {}
                
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
                        
                        
                @self.command(name="dice")
                async def roll_dice(ctx: commands.Context, sides: int = 6):
                    try:
                        result = random.randint(1, sides)
                        await ctx.send(f"@{ctx.author.name} rolled a {result}!")
                    except ValueError:
                        await ctx.send(f"@{ctx.author.name} please provide a valid number for sides!")




            async def event_ready(self):
                await asyncio.sleep(5)
                print(f'Logged into twitch | {self.nick}')


            async def event_message(self, message):
                try:
                    # Check if message and author exist
                    if message and message.author:
                        self.parent_cog.channel_last_message[message.channel.name] = {
                            'author': message.author.name,
                            'content': message.content,
                            'timestamp': time.time()
                        }

                except Exception as e:
                    print(f"Error in event_message: {e}")                             
                
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







    @tasks.loop(seconds=10)
    async def auto_message_task(self):
        if not hasattr(self, 'config'):
            return
                    
        for channel_name in self.config.get('channels', {}).keys():
            channel = self.twitch_bot.get_channel(channel_name)
            if channel:
                stream = await self.twitch_bot.fetch_streams(user_logins=[channel_name])
                
                if stream:
                    last_message = self.channel_last_message.get(channel_name)
                    
                    should_send = True
                    if last_message and 'author' in last_message:
                        if last_message['author'].lower() in [self.twitch_bot.nick.lower(), channel_name.lower()]:
                            should_send = False

                    if should_send:
                        messages = self.config['auto_messages'].get(channel_name, [])
                        
                        if not messages and 'default' in self.config['auto_messages']:
                            messages = self.config['auto_messages']['default']
                        
                        if messages:
                            message = random.choice(messages)
                            if self.last_messages.get(channel_name) != message:
                                await channel.send(message)
                                self.channel_last_message[channel_name] = {
                                    'author': self.twitch_bot.nick,
                                    'content': message,
                                    'timestamp': time.time()
                                }
                                self.last_messages[channel_name] = message






async def setup(bot):
    await bot.add_cog(TwitchCog(bot))
