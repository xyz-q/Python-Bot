import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

TICKETS_FILE = ".json/tickets.json"

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

class TicketModal(discord.ui.Modal, title="Ticket Submission"):
    subject = discord.ui.TextInput(label="Subject", style=discord.TextStyle.short, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        subject = self.subject.value
        description = self.description.value
        if interaction.guild:
            if isinstance(interaction.channel, discord.DMChannel):
                await interaction.response.send_message("Slash commands are not available in DMs.", ephemeral=True, delete_after=8)
                return

            ticket_channel = discord.utils.get(interaction.guild.text_channels, name="tickets")
            if ticket_channel is not None:
                embed = discord.Embed(title="New Ticket", color=discord.Color.dark_grey())
                embed.add_field(name="Subject", value=subject, inline=False)
                embed.add_field(name="Description", value=description, inline=False)
                embed.add_field(name="Submitted by", value=interaction.user.name, inline=False)
                view = TicketButtons(interaction.user.id, subject, description)
                await ticket_channel.send(embed=embed, view=view)
                await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True, delete_after=8)
            else:
                await interaction.response.send_message("Ticket channel not found. Please contact an administrator.",
                                                        ephemeral=True, delete_after=8)
        else:
            await interaction.response.send_message("Tickets have to be sent in a guild, silly! :3 /setup for more info",
                                                    ephemeral=True, delete_after=8)

class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user_id: int, subject: str, description: str):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.subject = subject
        self.description = description

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="ticket_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        ticket_user = guild.get_member(self.ticket_user_id)
        if not ticket_user:
            await interaction.response.send_message("User not found in server.", ephemeral=True)
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
            name=f"Ticket-{ticket_user.name}",
            overwrites=overwrites,
            reason="New ticket accepted"
        )
        await category.edit(position=len(guild.categories))  
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{ticket_user.name}",
            topic=f"Support ticket for {ticket_user.name}",
            reason="New ticket accepted"
        )
        
        # Save ticket data
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
            content=f"Hello {ticket_user.mention}, a support member will be with you shortly.",
            embed=embed, view=close_view)
        await interaction.response.send_message(f"Ticket accepted and channel created: {ticket_channel.mention}",
                                                ephemeral=True, delete_after=8)
        await interaction.message.delete()
        try:
            await ticket_user.send(f"Ticket accepted {ticket_channel.mention} by {interaction.user.name}.")
        except:
            pass

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, custom_id="ticket_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            ticket_user = interaction.guild.get_member(self.ticket_user_id)
            if ticket_user:
                try:
                    await ticket_user.send(f"Your ticket has been rejected by {interaction.user.name}.")
                except:
                    pass
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You do not have permission to reject this ticket.", ephemeral=True, delete_after=8)

class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_user_id: int, channel_id: int):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.channel_id = channel_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            # Update ticket status
            update_ticket_status(self.channel_id, "closed", interaction.user.id)
            
            ticket_user = interaction.guild.get_member(self.ticket_user_id)
            if ticket_user:
                try:
                    await ticket_user.send(f"Your ticket has been closed by {interaction.user.name}.")
                except:
                    pass
            await interaction.response.send_message("Ticket will be deleted in 5 seconds...", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete(reason="Ticket closed by support staff")
            category = interaction.channel.category
            if category and len(category.channels) == 0:
                await category.delete(reason="Category empty after ticket closed")
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True, delete_after=8)

class ticketcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketButtons(0, "", ""))  # Persistent view
        self.bot.add_view(CloseTicketButton(0, 0))  # Persistent view

    @app_commands.command(name="ticket", description="Submit a support ticket")
    async def ticket_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal())
    
    @app_commands.command(name="tickets", description="View ticket history")
    async def view_tickets(self, interaction: discord.Interaction, user: discord.Member = None):
        tickets = load_tickets()
        guild_tickets = [t for t in tickets.values() if t["guild_id"] == interaction.guild.id]
        
        if user:
            guild_tickets = [t for t in guild_tickets if t["user_id"] == user.id]
            title = f"Tickets for {user.display_name}"
        else:
            title = "All Server Tickets"
        
        if not guild_tickets:
            await interaction.response.send_message("No tickets found.", ephemeral=True)
            return
        
        embed = discord.Embed(title=title, color=discord.Color.blue())
        for ticket in guild_tickets[-10:]:  # Last 10 tickets
            user_obj = interaction.guild.get_member(ticket["user_id"])
            username = user_obj.display_name if user_obj else f"User {ticket['user_id']}"
            status = ticket.get("status", "unknown")
            created = ticket.get("created_at", "Unknown")[:10]
            embed.add_field(
                name=f"{ticket['subject']} - {status.title()}",
                value=f"By: {username}\nCreated: {created}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ticketcmd(bot))
    print("✓ Ticket command loaded successfully")
