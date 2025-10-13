import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

TICKETS_FILE = ".json/ticket_logs.json"

def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_ticket(ticket_data):
    tickets = load_tickets()
    tickets[str(ticket_data["channel_id"])] = ticket_data
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def update_ticket_status(channel_id, status, closed_by=None):
    tickets = load_tickets()
    if str(channel_id) in tickets:
        tickets[str(channel_id)]["status"] = status
        if closed_by:
            tickets[str(channel_id)]["closed_by"] = closed_by
            tickets[str(channel_id)]["closed_at"] = datetime.now().isoformat()
        with open(TICKETS_FILE, 'w') as f:
            json.dump(tickets, f, indent=2)

def is_ticket_channel(channel_id):
    tickets = load_tickets()
    return str(channel_id) in tickets

def has_active_ticket(user_id, guild_id):
    tickets = load_tickets()
    for ticket in tickets.values():
        if isinstance(ticket, dict):
            if (ticket.get("user_id") == user_id and 
                ticket.get("guild_id") == guild_id and 
                ticket.get("status") == "open"):
                return True
    return False

class TicketModal(discord.ui.Modal, title="Ticket Submission"):
    subject = discord.ui.TextInput(label="Subject", style=discord.TextStyle.short, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            print(f"Modal submitted by {interaction.user.name}")
            subject = self.subject.value
            description = self.description.value
            
            ticket_channel = discord.utils.get(interaction.guild.text_channels, name="tickets")
            if ticket_channel:
                embed = discord.Embed(title="New Ticket", color=discord.Color.dark_grey())
                embed.add_field(name="Subject", value=subject, inline=False)
                embed.add_field(name="Description", value=description, inline=False)
                embed.add_field(name="Submitted by", value=interaction.user.name, inline=False)
                view = TicketButtons(interaction.user.id, subject, description)
                await ticket_channel.send(embed=embed, view=view)
                await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True, delete_after=8)
                print("Ticket submitted successfully")
            else:
                await interaction.response.send_message("Ticket channel not found.", ephemeral=True, delete_after=8)
                print("Ticket channel not found")
        except Exception as e:
            print(f"Error in modal submission: {e}")
            try:
                await interaction.response.send_message(f"Error submitting ticket: {e}", ephemeral=True)
            except:
                pass

class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user_id: int = 0, subject: str = "", description: str = ""):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.subject = subject
        self.description = description

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="persistent:ticket_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if has_active_ticket(self.ticket_user_id, interaction.guild.id):
            await interaction.followup.send("This user already has an active ticket.", ephemeral=True)
            return
            
        guild = interaction.guild
        ticket_user = guild.get_member(self.ticket_user_id)
        if not ticket_user:
            await interaction.followup.send("User not found.", ephemeral=True)
            return
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ticket_user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        support_role = discord.utils.get(guild.roles, name=".trusted")  
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True)
        
        category = await guild.create_category(
            name=f"{ticket_user.name}-ticket",
            overwrites=overwrites,
            reason="New ticket accepted"
        )
        ticket_channel = await category.create_text_channel(
            name=f"{ticket_user.name}-support",
            topic=f"Support ticket for {ticket_user.name}",
            reason="New ticket accepted"
        )
        
        ticket_data = {
            "guild_id": guild.id,
            "user_id": self.ticket_user_id,
            "channel_id": ticket_channel.id,
            "category_id": category.id,
            "subject": self.subject,
            "description": self.description,
            "created_at": datetime.now().isoformat(),
            "accepted_by": interaction.user.id,
            "status": "open"
        }
        save_ticket(ticket_data)
        
        embed = discord.Embed(title="Ticket Details", color=discord.Color.dark_grey())
        embed.add_field(name="Subject", value=self.subject, inline=False)
        embed.add_field(name="Description", value=self.description, inline=False)
        embed.add_field(name="Submitted by", value=ticket_user.name, inline=False)
        
        close_view = CloseTicketButton(self.ticket_user_id, ticket_channel.id)
        await ticket_channel.send(
            content=f"Hello {ticket_user.mention}, support will be with you shortly.",
            embed=embed, view=close_view)
        await interaction.followup.send(f"Ticket created: {ticket_channel.mention}", ephemeral=True)
        await interaction.message.delete()
        
        try:
            await ticket_user.send(f"Ticket accepted: {ticket_channel.mention}")
        except:
            pass

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, custom_id="persistent:ticket_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            ticket_user = interaction.guild.get_member(self.ticket_user_id)
            if ticket_user:
                try:
                    await ticket_user.send(f"Your ticket was rejected by {interaction.user.name}.")
                except:
                    pass
            await interaction.message.delete()
        else:
            await interaction.response.send_message("No permission.", ephemeral=True)

class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_user_id: int = 0, channel_id: int = 0):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.channel_id = channel_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="persistent:ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            update_ticket_status(self.channel_id, "closed", interaction.user.id)
            
            ticket_user = interaction.guild.get_member(self.ticket_user_id)
            if ticket_user:
                try:
                    await ticket_user.send(f"Ticket closed by {interaction.user.name}.")
                except:
                    pass
            
            await interaction.response.send_message("Closing in 5 seconds...", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete(reason="Ticket closed")
            
            category = interaction.channel.category
            if category and len(category.channels) == 0:
                await category.delete(reason="Empty category")
        else:
            await interaction.response.send_message("No permission.", ephemeral=True)

class ticketcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketButtons())
        self.bot.add_view(CloseTicketButton())

    @app_commands.command(name="ticket", description="Submit a support ticket")
    async def ticket_command(self, interaction: discord.Interaction):
        try:
            print(f"Ticket command used by {interaction.user.name}")
            
            if has_active_ticket(interaction.user.id, interaction.guild.id):
                await interaction.response.send_message("You already have an active ticket.", ephemeral=True)
                return
            
            await interaction.response.send_modal(TicketModal())
            print("Modal sent successfully")
        except Exception as e:
            print(f"Error in ticket command: {e}")
            try:
                await interaction.response.send_message(f"Error: {e}", ephemeral=True)
            except:
                await interaction.followup.send(f"Error: {e}", ephemeral=True)
    
    @commands.command(name="ticketadd")
    async def ticket_add(self, ctx, member: discord.Member):
        if not is_ticket_channel(ctx.channel.id):
            await ctx.send("This command only works in ticket channels.")
            return
        
        trusted_role = discord.utils.get(ctx.guild.roles, name=".trusted")
        if trusted_role not in ctx.author.roles:
            await ctx.send("You don't have permission to add users to tickets.")
            return
        
        overwrites = ctx.channel.overwrites
        overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        await ctx.channel.edit(overwrites=overwrites)
        await ctx.send(f"{member.mention} has been added to this ticket.")
    
    @commands.command(name="ticketlogs")
    async def ticket_logs(self, ctx, user: discord.Member = None):
        tickets = load_tickets()
        guild_tickets = [t for t in tickets.values() if t.get("guild_id") == ctx.guild.id]
        
        if user:
            guild_tickets = [t for t in guild_tickets if t.get("user_id") == user.id]
            title = f"Tickets for {user.display_name}"
        else:
            title = f"All Tickets for {ctx.guild.name}"
        
        if not guild_tickets:
            await ctx.send("No tickets found.")
            return
        
        embed = discord.Embed(title=title, color=discord.Color.blue())
        for ticket in guild_tickets[-10:]:
            user_obj = ctx.guild.get_member(ticket.get("user_id", 0))
            username = user_obj.display_name if user_obj else f"User {ticket.get('user_id', 'Unknown')}"
            status = ticket.get("status", "unknown")
            created = ticket.get("created_at", "Unknown")[:10]
            embed.add_field(
                name=f"{ticket.get('subject', 'No Subject')} - {status.title()}",
                value=f"By: {username}\nCreated: {created}",
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ticketcmd(bot))