import discord
from discord.ext import commands

TICKET_CHANNEL_ID = 1241495094205354104 
WELCOME_CHANNEL_NAME = "welcome" 
ROLE_ID = 1056996133081186395 
GUILD_ID = 1056994840925192252 
active_tickets = {}

class WelcomeTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(AcceptDeclineView())
        self.bot.add_view(OkayView())

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == GUILD_ID:
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
                    okay_view = OkayView()
                    await cancel_message.edit(view=okay_view)
            else:
                print("Error: Could not find the specified channel for ticket messages.")



    async def send_ticket_message(self, member: discord.Member, guild: discord.Guild):
        me2 = await self.bot.fetch_user(110927272210354176) 
        ticket_channel = self.bot.get_channel(TICKET_CHANNEL_ID)
        if ticket_channel:
            embed = discord.Embed(
                title="New Member Request",
                description=f"{member.mention} has joined the server. Would you like to accept or decline their request?",
                color=discord.Color.gold()
            )
            message = await ticket_channel.send(embed=embed)
            view = AcceptDeclineView(member.id)
            await message.edit(view=view)

            active_tickets[member.id] = message

            await me2.send(f"New User Join {ticket_channel.mention}.")
        else:
            print("Error: Could not find the specified channel for ticket messages.")



class AcceptDeclineView(discord.ui.View):
    def __init__(self, user_id: int = 0):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="persistent:welcome_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        user = guild.get_member(self.user_id)
        
        # If user_id is 0 (after restart), extract from embed
        if not user and self.user_id == 0:
            embed = interaction.message.embeds[0] if interaction.message.embeds else None
            print(f"Debug: embed exists: {embed is not None}")
            if embed:
                print(f"Debug: embed description: {embed.description}")
                # Extract user mention from description
                import re
                match = re.search(r'<@!?(\d+)>', embed.description)
                if match:
                    user_id = int(match.group(1))
                    print(f"Debug: extracted user_id: {user_id}")
                    user = guild.get_member(user_id)
                    print(f"Debug: found user: {user}")
                    self.user_id = user_id
                else:
                    print("Debug: no user mention found in description")
        
        if not user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return
            
        role = guild.get_role(ROLE_ID)
        if role:
            await user.add_roles(role)
            embed = discord.Embed(
                title="Welcome to the Server!",
                description="Your request for the server `xyz` has been accepted, enjoy your stay!",
                color=discord.Color.green()
            )
            try:
                await user.send(embed=embed)
            except:
                pass
        
        await interaction.message.delete()
        active_tickets.pop(self.user_id, None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, custom_id="persistent:welcome_decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        user = guild.get_member(self.user_id)
        
        # If user_id is 0 (after restart), extract from embed
        if not user and self.user_id == 0:
            embed = interaction.message.embeds[0] if interaction.message.embeds else None
            if embed and embed.description:
                import re
                match = re.search(r'<@!?(\d+)>', embed.description)
                if match:
                    user_id = int(match.group(1))
                    user = guild.get_member(user_id)
                    self.user_id = user_id
        
        if user:
            try:
                await user.send("Access to the server has been declined by an Admin.")
            except:
                pass
            await user.kick(reason="Declined membership.")
        
        await interaction.message.delete()
        active_tickets.pop(self.user_id, None)

class OkayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Okay", style=discord.ButtonStyle.primary, custom_id="persistent:welcome_okay")
    async def okay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


async def setup(bot):
    await bot.add_cog(WelcomeTicket(bot))
