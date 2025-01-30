import discord
from discord.ext import commands

class ServerVoiceJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.dm_only()
    @commands.command()
    async def serverjoin(self, ctx, server_id: int, channel_id: int = None):
        try:
            # Get the guild
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send("Server not found! Please check the server ID.")
                return

            # If no channel_id is provided, find the first voice channel
            if channel_id is None:
                voice_channels = guild.voice_channels
                if not voice_channels:
                    await ctx.send("No voice channels found in this server!")
                    return
                channel = voice_channels[0]
            else:
                channel = guild.get_channel(channel_id)
                if not channel or not isinstance(channel, discord.VoiceChannel):
                    await ctx.send("Voice channel not found! Please check the channel ID.")
                    return

            # Check if bot has permission to join the voice channel
            permissions = channel.permissions_for(guild.me)
            if not permissions.connect:
                await ctx.send("I don't have permission to join that voice channel!")
                return

            # Connect to the voice channel
            try:
                await channel.connect()
                await ctx.send(f"Successfully joined voice channel: {channel.name} in {guild.name}")
            except discord.ClientException:
                # If already connected to a voice channel in this guild
                for vc in self.bot.voice_clients:
                    if vc.guild.id == guild.id:
                        await vc.disconnect()
                        await channel.connect()
                        await ctx.send(f"Switched to voice channel: {channel.name} in {guild.name}")
                        return

        except discord.Forbidden:
            await ctx.send("I don't have permission to join voice channels in that server!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @serverjoin.error
    async def serverjoin_error(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in DMs!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the server ID!\n"
                         "Usage: ,serverjoin <server_id> [channel_id]")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide valid server and channel IDs (numbers only)!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

    @commands.dm_only()
    @commands.command()
    async def voiceinfo(self, ctx, server_id: int):
        """Shows information about users in voice channels for the specified server"""
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send("Server not found! Please check the server ID.")
                return

            embed = discord.Embed(
                title=f"Voice Channels in {guild.name}",
                color=discord.Color.gold()
            )

            # Get all voice channels and their members
            voice_channels = guild.voice_channels
            if not voice_channels:
                await ctx.send("No voice channels found in this server!")
                return

            total_users = 0
            for vc in voice_channels:
                # Get members in the voice channel
                members = vc.members
                member_list = []
                
                for member in members:
                    status = []
                    if member.voice.self_mute:
                        status.append("🔇")  # Self muted
                    if member.voice.self_deaf:
                        status.append("🔕")  # Self deafened
                    if member.voice.mute:
                        status.append("🚫")  # Server muted
                    if member.voice.deaf:
                        status.append("❌")  # Server deafened
                    
                    member_status = f"{member.name} {''.join(status)}"
                    member_list.append(member_status)
                    total_users += 1

                # Create field for each voice channel
                if member_list:
                    members_text = "\n".join(member_list)
                    embed.add_field(
                        name=f"{vc.name} ({len(members)} users) - ID: {vc.id}",
                        value=members_text or "No users",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"{vc.name} (Empty) - ID: {vc.id}",
                        value="No users",
                        inline=False
                    )

            embed.set_footer(text=f"Total users in voice: {total_users}")
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("I don't have permission to view voice channels in that server!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @voiceinfo.error
    async def voiceinfo_error(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in DMs!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the server ID!\n"
                         "Usage: ,voiceinfo <server_id>")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid server ID (numbers only)!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")


async def setup(bot):
    await bot.add_cog(ServerVoiceJoin(bot))
