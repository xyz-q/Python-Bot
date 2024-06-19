import discord
from discord.ext import commands


class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command: Disconnect (Disconnect users from channel)
    @commands.command()
    async def disconnect(self, ctx, *members: discord.Member):
        if not members:
            await ctx.send("Please mention one or more users to disconnect.")
            return

        disconnected_members = []
        for member in members:
            if not member.voice:
                await ctx.send(f"{member.display_name} is not in a voice channel.")
                continue
            try:
                # Move member to a non-existent voice channel (disconnect them)
                await member.move_to(None)
                disconnected_members.append(member.display_name)
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to disconnect {member.display_name} from their voice channel.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to disconnect {member.display_name}.")

        if disconnected_members:
            await ctx.send(f"Disconnected {', '.join(disconnected_members)} from their voice channels.")

    # Command: Join (Connect to a voice channel)
    @commands.command()
    async def join(self, ctx, *, channel_keyword: str = None):
        # Disconnect from the current voice channel, if any
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

        if channel_keyword:
            # Check if the keyword matches any voice channel name in the guild
            matched_channels = [channel for channel in ctx.guild.voice_channels if
                                channel_keyword.lower() in channel.name.lower()]

            if not matched_channels:
                await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
                return

            # If multiple channels match, ask the user to specify further
            if len(matched_channels) > 1:
                await ctx.send(f"Multiple voice channels match the keyword '{channel_keyword}'. Please specify further.")
                return

            channel = matched_channels[0]
        else:
            # If no keyword provided, use the channel of the command invoker
            if ctx.author.voice is None or ctx.author.voice.channel is None:
                await ctx.send("You need to be in a voice channel to use this command.")
                return
            channel = ctx.author.voice.channel

        # Connect to the voice channel
        await channel.connect()
        await ctx.send(f"Joined {channel.name}")

    # Command: Gather (Move all members to a specified channel)
    @commands.command()
    async def gather(self, ctx, target_channel_keyword: str = None):
        # Check if the command invoker is in a voice channel
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel to use this command or specify a target channel!")
            return

        # If no target channel keyword is specified, use the invoker's channel
        if target_channel_keyword is None:
            target_channel = ctx.author.voice.channel
        else:
            # Find the target voice channel using the keyword
            matched_channels = [channel for channel in ctx.guild.voice_channels if
                                target_channel_keyword.lower() in channel.name.lower()]

            if not matched_channels:
                await ctx.send(f"No voice channel matching the keyword '{target_channel_keyword}' found.")
                return

            # If multiple channels match, ask the user to specify further
            if len(matched_channels) > 1:
                await ctx.send(
                    f"Multiple voice channels match the keyword '{target_channel_keyword}'. Please specify further.")
                return

            target_channel = matched_channels[0]

        # Get all voice channels in the guild
        voice_channels = ctx.guild.voice_channels

        # Iterate over each voice channel
        for channel in voice_channels:
            # Check if the channel is not the target channel
            if channel != target_channel:
                # Iterate over each member in the voice channel
                for member in channel.members:
                    # Move the member to the target channel
                    await member.move_to(target_channel)

        await ctx.send(f"All members have been gathered to {target_channel.mention}.")

    # Command: Drag (Move specific members to a specified channel)
    @commands.command()
    async def drag(self, ctx, channel_keyword: str, *members: discord.Member):
        # Find the target voice channel using the keyword
        matched_channels = [channel for channel in ctx.guild.voice_channels if
                            channel_keyword.lower() in channel.name.lower()]

        if not matched_channels:
            await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
            return

        # If multiple channels match, ask the user to specify further
        if len(matched_channels) > 1:
            await ctx.send(f"Multiple voice channels match the keyword '{channel_keyword}'. Please specify further.")
            return

        target_channel = matched_channels[0]

        if not members:
            await ctx.send("Please mention one or more users to drag.")
            return

        moved_members = []
        for member in members:
            if not member.voice:
                await ctx.send(f"{member.display_name} is not in a voice channel.")
                continue
            try:
                await member.move_to(target_channel)
                moved_members.append(member.display_name)
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to drag {member.display_name} to {target_channel.name}.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to drag {member.display_name}.")

        if moved_members:
            await ctx.send(f"Dragged {', '.join(moved_members)} to {target_channel.name}")

    # Command: Deafen (Deafen a member in a voice channel)
    @commands.command()
    async def deafen(self, ctx, target: str = None):
        # If no target is specified, default to the invoking user
        if target is None:
            target = ctx.author
        # If target is "bot", set it to the bot user
        elif target.lower() == "bot":
            target = ctx.guild.me
        else:
            # Attempt to find the member with the given name or mention
            target = discord.utils.get(ctx.guild.members, name=target)
            if target is None:
                await ctx.send("Target not found.")
                return

        # Check if the target user is in a voice channel
        if not target.voice:
            await ctx.send(f"{target.display_name} is not in a voice channel.")
            return

        # Check if the user invoking the command has permission to deafen members
        if not ctx.author.guild_permissions.deafen_members:
            await ctx.send("You do not have permission to deafen members.")
            return

        # Check if the bot has permission to deafen members
        if not ctx.guild.me.guild_permissions.deafen_members:
            await ctx.send("I do not have permission to deafen members.")
            return

        # Toggle the deafen status of the target user
        deafened = not target.voice.deaf
        await target.edit(deafen=deafened)

        # Send a message indicating the deafen status
        if deafened:
            await ctx.send(f"{target.display_name} has been deafened.")
        else:
            await ctx.send(f"{target.display_name} has been undeafened.")

    # Error handling for missing permissions
    @deafen.error
    async def deafen_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, you do not have permission to do that.")

    # Command: Mute (Mute a member in a voice channel)
    @commands.command()
    async def mute(self, ctx, target: discord.Member = None):
        # If no target is specified, send an error message
        if target is None:
            await ctx.send("Please specify a user to mute.")
            return

        # Check if the user invoking the command has permission to mute members
        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("You do not have permission to mute members.")
            return

        # Check if the bot has permission to mute members
        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send("I do not have permission to mute members.")
            return

        # Toggle the mute status of the target user
        muted = not target.voice.mute
        await target.edit(mute=muted)

        # Send a message indicating the mute status
        if muted:
            await ctx.send(f"{target.display_name} has been muted.")
        else:
            await ctx.send(f"{target.display_name} has been unmuted.")

    # Error handling for missing permissions and missing target
    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, you do not have permission to do that.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a user to mute.")


async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
