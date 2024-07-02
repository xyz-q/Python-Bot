import discord
from discord.ext import commands


class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                await member.move_to(None)
                disconnected_members.append(member.display_name)
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to disconnect {member.display_name} from their voice channel.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to disconnect {member.display_name}.")

        if disconnected_members:
            await ctx.send(f"Disconnected {', '.join(disconnected_members)} from their voice channels.")

    @commands.command()
    async def join(self, ctx, *, channel_keyword: str = None):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        if channel_keyword:
            matched_channels = [channel for channel in ctx.guild.voice_channels if
                                channel_keyword.lower() in channel.name.lower()]
            if not matched_channels:
                await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
                return

            if len(matched_channels) > 1:
                await ctx.send(f"Multiple voice channels match the keyword '{channel_keyword}'. Please specify further.")
                return

            channel = matched_channels[0]
        else:
            if ctx.author.voice is None or ctx.author.voice.channel is None:
                await ctx.send("You need to be in a voice channel to use this command.")
                return
            channel = ctx.author.voice.channel

        await channel.connect()
        await ctx.send(f"Joined {channel.name}")

    @commands.command()
    async def gather(self, ctx, target_channel_keyword: str = None):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in a voice channel to use this command or specify a target channel!")
            return

        if target_channel_keyword is None:
            target_channel = ctx.author.voice.channel
        else:
            matched_channels = [channel for channel in ctx.guild.voice_channels if
                                target_channel_keyword.lower() in channel.name.lower()]

            if not matched_channels:
                await ctx.send(f"No voice channel matching the keyword '{target_channel_keyword}' found.")
                return

            if len(matched_channels) > 1:
                await ctx.send(
                    f"Multiple voice channels match the keyword '{target_channel_keyword}'. Please specify further.")
                return

            target_channel = matched_channels[0]

        voice_channels = ctx.guild.voice_channels
        for channel in voice_channels:
            if channel != target_channel:
                for member in channel.members:
                    await member.move_to(target_channel)

        await ctx.send(f"All members have been gathered to {target_channel.mention}.")

    @commands.command()
    async def drag(self, ctx, channel_keyword: str, *members: discord.Member):
        matched_channels = [channel for channel in ctx.guild.voice_channels if
                            channel_keyword.lower() in channel.name.lower()]

        if not matched_channels:
            await ctx.send(f"No voice channel matching the keyword '{channel_keyword}' found.")
            return

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

    @commands.command()
    async def deafen(self, ctx, target: str = None):
        if target is None:
            target = ctx.author
        elif target.lower() == "bot":
            target = ctx.guild.me
        else:
            target = discord.utils.get(ctx.guild.members, name=target)
            if target is None:
                await ctx.send("Target not found.")
                return

        if not target.voice:
            await ctx.send(f"{target.display_name} is not in a voice channel.")
            return

        if not ctx.author.guild_permissions.deafen_members:
            await ctx.send("You do not have permission to deafen members.")
            return

        if not ctx.guild.me.guild_permissions.deafen_members:
            await ctx.send("I do not have permission to deafen members.")
            return

        deafened = not target.voice.deaf
        await target.edit(deafen=deafened)

        if deafened:
            await ctx.send(f"{target.display_name} has been deafened.")
        else:
            await ctx.send(f"{target.display_name} has been undeafened.")

    @deafen.error
    async def deafen_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, you do not have permission to do that.")

    @commands.command()
    async def mute(self, ctx, target: discord.Member = None):
        if target is None:
            await ctx.send("Please specify a user to mute.")
            return

        if not ctx.author.guild_permissions.mute_members:
            await ctx.send("You do not have permission to mute members.")
            return

        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send("I do not have permission to mute members.")
            return

        muted = not target.voice.mute
        await target.edit(mute=muted)

        if muted:
            await ctx.send(f"{target.display_name} has been muted.")
        else:
            await ctx.send(f"{target.display_name} has been unmuted.")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, you do not have permission to do that.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a user to mute.")

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
