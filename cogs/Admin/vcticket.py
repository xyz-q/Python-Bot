import asyncio
import os
import discord
from discord.ext import commands

TICKET_CHANNEL_ID = 1241495094205354104
GUILD_ID = 1056994840925192252
active_tickets = {}

class VCTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(self.AcceptDeclineView2())
        self.bot.add_view(self.OkayView2())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user:
            if before.channel != after.channel:
                if after.channel is not None:

                    await asyncio.sleep(1.5)
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    mp3_file = os.path.join(current_dir, '.mp3', 'uwu.mp3')
                    if not os.path.exists(mp3_file):
                        print("uwu.mp3 file not found.")
                        return
                    try:
                        if not self.bot.voice_clients:
                            voice_client = await after.channel.connect()
                        else:
                            voice_client = self.bot.voice_clients[0]

                        if not voice_client.is_playing():
                            voice_client.play(discord.FFmpegPCMAudio(mp3_file))
                            while voice_client.is_playing():
                                await asyncio.sleep(1)
                    except Exception as e:
                        print(f"Error playing mp3: {e}")

        if member.bot or member == self.bot.user or member.id == 110927272210354176:
            return

        if before.channel is None and after.channel is not None:
            if after.channel.name == '.waiting-room':
                await self.send_voice_request_message(member, member.guild)
        elif before.channel and before.channel.name == '.waiting-room' and (not after.channel or after.channel.name != '.waiting-room'):
            await self.cancel_voice_request(member, member.guild)





    async def send_voice_request_message(self, member: discord.Member, guild: discord.Guild):
        me = await self.bot.fetch_user(110927272210354176)
        ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
        if ticket_channel:
            embed = discord.Embed(
                title=".waiting-room",
                description=f"{member.mention} has joined the waiting room. Drag them to ,main?",
                color=discord.Color.gold()
            )
            message = await ticket_channel.send(embed=embed)
            view = self.AcceptDeclineView2(member.id)
            await message.edit(view=view)
            active_tickets[member.id] = message
            await me.send(f"A user has joined the waiting room {ticket_channel.mention}.")
        else:
            print("Error: Could not find the specified channel for ticket messages.")

    async def cancel_voice_request(self, member: discord.Member, guild: discord.Guild):
        if member.id in active_tickets:
            message = active_tickets.pop(member.id)
            ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
            if ticket_channel:
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass

                embed = discord.Embed(
                    title="Ticket Canceled",
                    description=f"The ticket for {member.mention} has been dealt with/canceled.",
                    color=discord.Color.red()
                )
                cancel_message = await ticket_channel.send(embed=embed)
                view = self.OkayView2()
                await cancel_message.edit(view=view)

    class AcceptDeclineView2(discord.ui.View):
        def __init__(self, member_id: int = 0):
            super().__init__(timeout=None)
            self.member_id = member_id

        @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="persistent:vc_accept")
        async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            guild = interaction.guild
            member = guild.get_member(self.member_id)
            
            # If member_id is 0 (after restart), extract from embed
            if not member and self.member_id == 0:
                embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if embed and embed.description:
                    import re
                    match = re.search(r'<@!?(\d+)>', embed.description)
                    if match:
                        member_id = int(match.group(1))
                        member = guild.get_member(member_id)
                        self.member_id = member_id
            
            if not member:
                await interaction.followup.send("User not found.", ephemeral=True)
                return
                
            waiting_room = discord.utils.get(guild.voice_channels, name=".waiting-room")
            main_channel = discord.utils.get(guild.voice_channels, name=",main")

            if not waiting_room:
                await interaction.followup.send("Waiting room channel not found.", ephemeral=True)
                return
            if not main_channel:
                await interaction.followup.send("Main channel not found.", ephemeral=True)
                return
                
            if not member.voice:
                await interaction.followup.send(f"{member.mention} is not in a voice channel.", ephemeral=True)
                return
                
            if member.voice.channel != waiting_room:
                await interaction.followup.send(f"{member.mention} is not in the waiting room.", ephemeral=True)
                return
                
            # Check bot permissions
            bot_member = guild.get_member(interaction.client.user.id)
            if not main_channel.permissions_for(bot_member).move_members:
                await interaction.followup.send("Bot lacks 'Move Members' permission in the main channel.", ephemeral=True)
                return
                
            try:
                await member.move_to(main_channel)
                await interaction.followup.send(f"Successfully moved {member.mention} to {main_channel.mention}.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("Bot lacks permission to move members.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"Failed to move member: {e}", ephemeral=True)
                return

            await interaction.message.delete()
            active_tickets.pop(self.member_id, None)

        @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, custom_id="persistent:vc_decline")
        async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            guild = interaction.guild
            member = guild.get_member(self.member_id)
            
            # If member_id is 0 (after restart), extract from embed
            if not member and self.member_id == 0:
                embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if embed and embed.description:
                    import re
                    match = re.search(r'<@!?(\d+)>', embed.description)
                    if match:
                        member_id = int(match.group(1))
                        member = guild.get_member(member_id)
                        self.member_id = member_id
            
            if member:
                waiting_room = discord.utils.get(guild.voice_channels, name=".waiting-room")
                if waiting_room and member.voice and member.voice.channel == waiting_room:
                    await member.move_to(None)

            await interaction.message.delete()
            active_tickets.pop(self.member_id, None)

        @discord.ui.button(label="Stay", style=discord.ButtonStyle.primary, custom_id="persistent:vc_stay")
        async def stay(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            # Extract member_id if needed
            if self.member_id == 0:
                embed = interaction.message.embeds[0] if interaction.message.embeds else None
                if embed and embed.description:
                    import re
                    match = re.search(r'<@!?(\d+)>', embed.description)
                    if match:
                        self.member_id = int(match.group(1))
            
            await interaction.message.delete()
            active_tickets.pop(self.member_id, None)

    class OkayView2(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary, custom_id="persistent:vc_okay")
        async def okay(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.message.delete()

async def setup(bot):
    await bot.add_cog(VCTicket(bot))
