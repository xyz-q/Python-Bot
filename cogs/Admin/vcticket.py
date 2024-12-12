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

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user:
            if before.channel != after.channel:
                if after.channel is not None:
                    print(f"The bot has joined voice channel: {after.channel.name}")
                    await asyncio.sleep(2)
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

        # Check if the user joined a voice channel
        if before.channel is None and after.channel is not None:
            if after.channel.name == '.waiting-room':
                await self.send_voice_request_message(member, member.guild)
        # Check if the user left the waiting room
        elif before.channel and before.channel.name == '.waiting-room' and (not after.channel or after.channel.name != '.waiting-room'):
            await self.cancel_voice_request(member, member.guild)

    @commands.command(name="vc_ticket", description="Open a voice channel ticket")
    async def vc_ticket(self, ctx):
        await ctx.send("Opening voice channel ticket...")
        await ctx.send(f"Voice channel ticket command executed by {ctx.author}")

    @commands.Cog.listener()
    async def on_ready(self):
        print("VCTicketCog is ready.")

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
            view = self.AcceptDeclineView2(member, guild, message)
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
                view = self.OkayView2(cancel_message)
                await cancel_message.edit(view=view)

    class AcceptDeclineView2(discord.ui.View):
        def __init__(self, member: discord.Member, guild: discord.Guild, message: discord.Message):
            super().__init__(timeout=None)
            self.member = member
            self.guild = guild
            self.message = message

        @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
        async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
            waiting_room = discord.utils.get(self.guild.voice_channels, name=".waiting-room")
            main_channel = discord.utils.get(self.guild.voice_channels, name=",main")

            if waiting_room and main_channel:
                if self.member.voice and self.member.voice.channel == waiting_room:
                    await self.member.move_to(main_channel)

            try:
                await self.message.delete()
            except discord.errors.NotFound:
                pass

            active_tickets.pop(self.member.id, None)

        @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
        async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
            waiting_room = discord.utils.get(self.guild.voice_channels, name=".waiting-room")
            if waiting_room:
                if self.member.voice and self.member.voice.channel == waiting_room:
                    await self.member.move_to(None)

            try:
                await self.message.delete()
            except discord.errors.NotFound:
                pass

        @discord.ui.button(label="Stay", style=discord.ButtonStyle.primary)
        async def stay(self, button: discord.ui.Button, interaction: discord.Interaction):
            waiting_room = discord.utils.get(self.guild.voice_channels, name=".waiting-room")
            if waiting_room:
                if self.member.voice and self.member.voice.channel == waiting_room:
                    await self.message.delete()

            try:
                await self.message.delete()
            except discord.errors.NotFound:
                pass

            active_tickets.pop(self.member.id, None)

    class OkayView2(discord.ui.View):
        def __init__(self, message: discord.Message):
            super().__init__(timeout=None)
            self.message = message

        @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary)
        async def okay(self, button: discord.ui.Button, interaction: discord.Interaction):
            await self.message.delete()

async def setup(bot):
    await bot.add_cog(VCTicket(bot))
