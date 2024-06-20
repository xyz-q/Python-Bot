import discord
from discord.ext import commands

# Constants
TICKET_CHANNEL_ID = 1241495094205354104 
WELCOME_CHANNEL_NAME = "welcome" 
ROLE_ID = 1056996133081186395 
GUILD_ID = 1056994840925192252 
active_tickets = {}

class WelcomeTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == GUILD_ID:
            await self.send_welcome_message(member)
            await self.send_ticket_message(member, member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id == GUILD_ID:
            if member.id in active_tickets:
                ticket_message = active_tickets.pop(member.id)
                try:
                    await ticket_message.delete()
                except discord.errors.NotFound:
                    pass

                me2 = await self.bot.fetch_user(110927272210354176) 
                await me2.send(f"The ticket for {member.mention} has been canceled as they have left/been kicked from the server.")

                ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
                if ticket_channel:
                    embed = discord.Embed(
                        title="Ticket Canceled",
                        description=f"The ticket for {member.mention} has been canceled as they have left/been kicked from the server.",
                        color=discord.Color.red()
                    )
                    cancel_message = await ticket_channel.send(embed=embed)
                    okay_view = OkayView(cancel_message)
                    await cancel_message.edit(view=okay_view)
            else:
                print("Error: Could not find the specified channel for ticket messages.")

            channel = discord.utils.get(member.guild.channels, name="exit", type=discord.ChannelType.text)
            if channel:
                embed = discord.Embed(
                    title=f"Goodbye, {member.display_name}!",
                    description="We'll miss you.",
                    color=discord.Color.dark_grey()
                )
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                embed.set_footer(text=f"User ID: {member.id}")
                await channel.send(embed=embed)
            else:
                print("Error: Could not find the specified channel for farewell messages.")

    async def send_ticket_message(self, member: discord.Member, guild: discord.Guild):
        me2 = await self.bot.fetch_user(110927272210354176)  # Replace with your Discord user ID
        ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
        if ticket_channel:
            embed = discord.Embed(
                title="New Member Request",
                description=f"{member.mention} has joined the server. Would you like to accept or decline their request?",
                color=discord.Color.gold()
            )
            message = await ticket_channel.send(embed=embed)
            view = AcceptDeclineView(member, guild, message)
            await message.edit(view=view)

            active_tickets[member.id] = message

            await me2.send(f"New User Join {ticket_channel.mention}.")
        else:
            print("Error: Could not find the specified channel for ticket messages.")

    async def send_welcome_message(self, member: discord.Member):
        channel = discord.utils.get(member.guild.channels, name=WELCOME_CHANNEL_NAME, type=discord.ChannelType.text)
        if channel:
            embed = discord.Embed(
                title=f"{member.display_name} pulled up",
                description=f"Username: {member.name}",
                color=discord.Color.red()
            )
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)
        else:
            print("Error: Could not find the specified channel for welcome messages.")

class AcceptDeclineView(discord.ui.View):
    def __init__(self, user: discord.Member, guild: discord.Guild, message: discord.Message):
        super().__init__(timeout=None)
        self.user = user
        self.guild = guild
        self.message = message

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        role = self.guild.get_role(ROLE_ID)
        if role and self.user:
            await self.user.add_roles(role)
            await self.user.send("Welcome to the server! Enjoy your stay.")
        try:
            await self.message.delete()
        except discord.errors.NotFound:
            pass
        active_tickets.pop(self.user.id, None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.user.kick(reason="Declined membership.")
        await self.user.send("Access to the server has been declined by an Admin.")
        try:
            await self.message.delete()
        except discord.errors.NotFound:
            pass
        active_tickets.pop(self.user.id, None)

class OkayView(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary)
    async def okay(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await self.message.delete()
        except discord.errors.NotFound:
            pass


async def setup(bot):
    await bot.add_cog(WelcomeTicket(bot))
