import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timezone

TICKETS_FILE = ".json/ticket_logs.json"
_json_lock = asyncio.Lock()


# --- JSON helpers (lock only wraps the file I/O, not callers) ---

def _read_tickets_sync() -> dict:
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return {}


def _write_tickets_sync(tickets: dict):
    os.makedirs(".json", exist_ok=True)
    tmp = TICKETS_FILE + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(tickets, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, TICKETS_FILE)


async def _read() -> dict:
    async with _json_lock:
        return _read_tickets_sync()


async def _write(tickets: dict):
    async with _json_lock:
        _write_tickets_sync(tickets)


async def _update(fn):
    """Read-modify-write under a single lock acquisition to prevent lost updates."""
    async with _json_lock:
        tickets = _read_tickets_sync()
        result = fn(tickets)
        if asyncio.iscoroutine(result):
            raise TypeError("_update callback must be synchronous, not a coroutine")
        _write_tickets_sync(tickets)


# --- Public ticket helpers ---

async def load_tickets() -> dict:
    return await _read()


async def save_ticket(ticket_data: dict):
    def _apply(t):
        t[str(ticket_data["channel_id"])] = ticket_data
    await _update(_apply)


async def update_ticket_status(channel_id: int, status: str, closed_by: int = None):
    def _apply(t):
        key = str(channel_id)
        if key not in t:
            return
        t[key]["status"] = status
        if closed_by:
            t[key]["closed_by"] = closed_by
            t[key]["closed_at"] = datetime.now(timezone.utc).isoformat()
    await _update(_apply)


async def is_ticket_channel(channel_id: int) -> bool:
    tickets = await _read()
    return str(channel_id) in tickets


_accept_lock = asyncio.Lock()


async def has_pending_ticket(user_id: int, guild_id: int) -> bool:
    tickets = await _read()
    return any(
        isinstance(t, dict) and t.get("status") == "pending"
        and t.get("user_id") == user_id and t.get("guild_id") == guild_id
        for t in tickets.values()
    )


async def has_active_ticket(user_id: int, guild_id: int, bot: discord.Client = None) -> bool:
    """
    Returns True if the user has an open ticket whose channel still exists.
    Uses fetch_channel to handle post-restart cache misses before marking closed.
    """
    tickets = await _read()
    for ticket in tickets.values():
        if not isinstance(ticket, dict):
            continue
        if ticket.get("status") != "open":
            continue
        if ticket.get("user_id") != user_id or ticket.get("guild_id") != guild_id:
            continue
        if bot is not None:
            channel_id = ticket.get("channel_id", 0)
            channel = bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await bot.fetch_channel(channel_id)
                except (discord.NotFound, discord.Forbidden):
                    await update_ticket_status(channel_id, "closed")
                    continue
                except discord.HTTPException:
                    # Network error — don't mark closed, assume it still exists
                    pass
        return True
    return False


async def save_pending_ticket(message_id: int, user_id: int, guild_id: int, subject: str, description: str):
    def _apply(t):
        t[f"pending_{message_id}"] = {
            "user_id": user_id,
            "guild_id": guild_id,
            "subject": subject,
            "description": description,
            "status": "pending"
        }
    await _update(_apply)


async def get_pending_ticket(message_id: int) -> dict | None:
    tickets = await _read()
    return tickets.get(f"pending_{message_id}")


async def remove_pending_ticket(message_id: int):
    def _apply(t):
        t.pop(f"pending_{message_id}", None)
    await _update(_apply)


TRANSCRIPTS_DIR = ".json/transcripts"


async def _save_transcript(channel: discord.TextChannel, channel_id: int):
    try:
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        messages = []
        async for msg in channel.history(limit=None, oldest_first=True):
            entry = {
                "timestamp": msg.created_at.isoformat(),
                "author": msg.author.display_name,
                "author_id": msg.author.id,
                "content": msg.content,
            }
            if msg.attachments:
                entry["attachments"] = [a.url for a in msg.attachments]
            if msg.embeds:
                entry["embeds"] = [e.title for e in msg.embeds if e.title]
            messages.append(entry)

        path = os.path.join(TRANSCRIPTS_DIR, f"ticket_{channel_id}.json")
        tmp = path + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception as e:
        print(f"Failed to save transcript for channel {channel_id}: {e}")


# --- Modals ---

class TicketModal(discord.ui.Modal, title="Ticket Submission"):
    subject = discord.ui.TextInput(label="Subject", style=discord.TextStyle.short, required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Tickets can only be submitted in a server.", ephemeral=True)
            return
        try:
            subject = self.subject.value
            description = self.description.value

            ticket_channel = discord.utils.get(interaction.guild.text_channels, name="tickets")
            if not ticket_channel:
                await interaction.response.send_message("Ticket channel not found.", ephemeral=True, delete_after=8)
                return

            embed = discord.Embed(title="New Ticket", color=discord.Color.dark_grey())
            embed.add_field(name="Subject", value=subject, inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="User ID", value=str(interaction.user.id), inline=False)
            embed.add_field(name="Submitted by", value=interaction.user.display_name, inline=False)

            view = TicketButtons(interaction.user.id, subject, description)
            message = await ticket_channel.send(embed=embed, view=view)
            await save_pending_ticket(message.id, interaction.user.id, interaction.guild.id, subject, description)
            await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True, delete_after=8)
        except Exception as e:
            print(f"Error in TicketModal.on_submit: {e}")
            try:
                await interaction.response.send_message(f"Error submitting ticket: {e}", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send(f"Error submitting ticket: {e}", ephemeral=True)


class AddUserModal(discord.ui.Modal, title="Add User to Ticket"):
    username = discord.ui.TextInput(
        label="Username or User ID", style=discord.TextStyle.short,
        required=True, placeholder="Enter username or user ID"
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        value = self.username.value
        member = None
        if value.isdigit():
            member = interaction.guild.get_member(int(value))
        else:
            member = (discord.utils.get(interaction.guild.members, name=value) or
                      discord.utils.get(interaction.guild.members, display_name=value))

        if not member:
            await interaction.response.send_message(f"User '{value}' not found.", ephemeral=True)
            return

        overwrites = self.channel.overwrites
        overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await self.channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"{member.mention} has been added to this ticket.")


# --- Views ---

class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user_id: int = 0, subject: str = "", description: str = ""):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.subject = subject
        self.description = description

    async def _recover_data(self, interaction: discord.Interaction) -> bool:
        pending = await get_pending_ticket(interaction.message.id)
        if pending:
            self.ticket_user_id = pending["user_id"]
            self.subject = pending["subject"]
            self.description = pending["description"]
            return True

        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            for field in embed.fields:
                if field.name == "User ID" and field.value.isdigit():
                    self.ticket_user_id = int(field.value)
                    self.subject = next((f.value for f in embed.fields if f.name == "Subject"), "No Subject")
                    self.description = next((f.value for f in embed.fields if f.name == "Description"), "No Description")
                    return True
        return False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="persistent:ticket_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role not in interaction.user.roles:
            await interaction.response.send_message("No permission.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if self.ticket_user_id == 0:
            if not await self._recover_data(interaction):
                await interaction.followup.send("Could not identify ticket user.", ephemeral=True)
                return

        # Serialize accept to prevent two staff members creating duplicate tickets simultaneously
        async with _accept_lock:
            if await has_active_ticket(self.ticket_user_id, interaction.guild.id, interaction.client):
                await interaction.followup.send("This user already has an active ticket.", ephemeral=True)
                return

            guild = interaction.guild
            ticket_user = guild.get_member(self.ticket_user_id)
            if not ticket_user:
                await interaction.followup.send("User not found in server.", ephemeral=True)
                return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ticket_user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True,
                    attach_files=True, embed_links=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True,
                    manage_channels=True, manage_messages=True,
                    attach_files=True, embed_links=True
                ),
            }
            support_role = discord.utils.get(guild.roles, name=".trusted")
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True,
                    manage_messages=True, manage_channels=True,
                    attach_files=True, embed_links=True
                )

            try:
                category = await guild.create_category(
                    name=f"ticket-{ticket_user.id}",
                    overwrites=overwrites,
                    reason="New ticket accepted"
                )
            except discord.Forbidden:
                await interaction.followup.send("Missing permission to create category.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"Failed to create ticket category: {e}", ephemeral=True)
                return

            try:
                ticket_channel = await category.create_text_channel(
                    name=f"support-{ticket_user.id}",
                    topic=f"Support ticket for {ticket_user.display_name} ({ticket_user.id})",
                    reason="New ticket accepted"
                )
            except discord.Forbidden:
                await interaction.followup.send("Missing permission to create ticket channel.", ephemeral=True)
                await category.delete(reason="Ticket channel creation failed")
                return
            except discord.HTTPException as e:
                await interaction.followup.send(f"Failed to create ticket channel: {e}", ephemeral=True)
                await category.delete(reason="Ticket channel creation failed")
                return

            ticket_data = {
                "guild_id": guild.id,
                "user_id": self.ticket_user_id,
                "channel_id": ticket_channel.id,
                "category_id": category.id,
                "subject": self.subject,
                "description": self.description,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "accepted_by": interaction.user.id,
                "status": "open"
            }
            await save_ticket(ticket_data)

        embed = discord.Embed(title="Ticket Details", color=discord.Color.dark_grey())
        embed.add_field(name="Subject", value=self.subject, inline=False)
        embed.add_field(name="Description", value=self.description, inline=False)
        embed.add_field(name="User ID", value=str(self.ticket_user_id), inline=False)
        embed.add_field(name="Submitted by", value=ticket_user.display_name, inline=False)

        close_view = CloseTicketButton(self.ticket_user_id, ticket_channel.id)
        try:
            await ticket_channel.send(
                content=f"Hello {ticket_user.mention}, support will be with you shortly.",
                embed=embed, view=close_view
            )
        except discord.HTTPException as e:
            print(f"Failed to send opening message in ticket {ticket_channel.id}: {e}")
        await interaction.followup.send(f"Ticket created: {ticket_channel.mention}", ephemeral=True)
        await remove_pending_ticket(interaction.message.id)
        await interaction.message.delete()

        try:
            await ticket_user.send(f"Your ticket has been accepted: {ticket_channel.mention}")
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, custom_id="persistent:ticket_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role not in interaction.user.roles:
            await interaction.response.send_message("No permission.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if self.ticket_user_id == 0:
            await self._recover_data(interaction)

        ticket_user = interaction.guild.get_member(self.ticket_user_id)
        if ticket_user:
            try:
                await ticket_user.send(f"Your ticket was rejected by {interaction.user.display_name}.")
            except discord.HTTPException:
                pass

        await remove_pending_ticket(interaction.message.id)
        await interaction.message.delete()


class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_user_id: int = 0, channel_id: int = 0):
        super().__init__(timeout=None)
        self.ticket_user_id = ticket_user_id
        self.channel_id = channel_id

    async def _recover_data(self, interaction: discord.Interaction) -> bool:
        self.channel_id = interaction.channel.id
        tickets = await _read()
        ticket = tickets.get(str(self.channel_id))
        if ticket:
            self.ticket_user_id = ticket.get("user_id", 0)
            return True
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            for field in embed.fields:
                if field.name == "User ID" and field.value.isdigit():
                    self.ticket_user_id = int(field.value)
                    return True
        return False

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="persistent:ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role not in interaction.user.roles:
            await interaction.response.send_message("No permission.", ephemeral=True)
            return

        if self.ticket_user_id == 0 or self.channel_id == 0:
            recovered = await self._recover_data(interaction)
            if not recovered or self.channel_id == 0:
                await interaction.response.send_message("Could not identify this ticket. It may already be closed.", ephemeral=True)
                return

        await update_ticket_status(self.channel_id, "closed", interaction.user.id)

        ticket_user = interaction.guild.get_member(self.ticket_user_id)
        if ticket_user:
            try:
                await ticket_user.send(f"Your ticket has been closed by {interaction.user.display_name}.")
            except discord.HTTPException:
                pass

        category = interaction.channel.category
        await interaction.response.send_message("Closing in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)

        await _save_transcript(interaction.channel, self.channel_id)

        try:
            await interaction.channel.delete(reason="Ticket closed")
        except discord.Forbidden:
            print(f"Missing permission to delete ticket channel {self.channel_id}")
            return
        except discord.HTTPException as e:
            print(f"Failed to delete ticket channel {self.channel_id}: {e}")
            return

        if category:
            try:
                if len(category.channels) == 0:
                    await category.delete(reason="Empty ticket category")
            except discord.HTTPException as e:
                print(f"Failed to delete ticket category: {e}")


# --- Cog ---

class ticketcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(TicketButtons())
        self.bot.add_view(CloseTicketButton())

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        tickets = await _read()
        key = f"pending_{payload.message_id}"
        if key in tickets:
            await remove_pending_ticket(payload.message_id)

    @app_commands.command(name="ticket", description="Submit a support ticket")
    async def ticket_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        try:
            if await has_pending_ticket(interaction.user.id, interaction.guild.id):
                await interaction.response.send_message("You already have a pending ticket.", ephemeral=True)
                return
            if await has_active_ticket(interaction.user.id, interaction.guild.id, interaction.client):
                await interaction.response.send_message("You already have an active ticket.", ephemeral=True)
                return
            await interaction.response.send_modal(TicketModal())
        except Exception as e:
            print(f"Error in /ticket: {e}")
            try:
                await interaction.response.send_message(f"Error: {e}", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="ticketadd", description="Add a user to this ticket")
    async def ticket_add(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        if not await is_ticket_channel(interaction.channel.id):
            await interaction.response.send_message("This command only works in ticket channels.", ephemeral=True)
            return
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role not in interaction.user.roles:
            await interaction.response.send_message("You don't have permission to add users to tickets.", ephemeral=True)
            return
        overwrites = interaction.channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        await interaction.channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"{user.mention} has been added to this ticket.")

    @app_commands.command(name="ticketlogs", description="View ticket history")
    async def ticket_logs(self, interaction: discord.Interaction, user: discord.Member = None, page: int = 1):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        tickets = await _read()
        guild_tickets = [
            t for t in tickets.values()
            if isinstance(t, dict)
            and t.get("guild_id") == interaction.guild.id
            and t.get("status") in ("open", "closed")
        ]

        if user:
            guild_tickets = [t for t in guild_tickets if t.get("user_id") == user.id]
            title = f"Tickets for {user.display_name}"
        else:
            title = f"All Tickets for {interaction.guild.name}"

        # Sort newest first
        guild_tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)

        if not guild_tickets:
            await interaction.response.send_message("No tickets found.", ephemeral=True)
            return

        per_page = 10
        total_pages = (len(guild_tickets) + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page

        embed = discord.Embed(title=f"{title} (Page {page}/{total_pages})", color=discord.Color.gold())
        for ticket in guild_tickets[start_idx:start_idx + per_page]:
            user_obj = interaction.guild.get_member(ticket.get("user_id", 0))
            username = user_obj.display_name if user_obj else f"User {ticket.get('user_id', 'Unknown')}"
            status = ticket.get("status", "unknown")
            created = ticket.get("created_at", "Unknown")[:10]
            embed.add_field(
                name=f"{ticket.get('subject', 'No Subject')} — {status.title()}",
                value=f"By: {username}\nCreated: {created}",
                inline=True
            )
        embed.set_footer(text=f"Total: {len(guild_tickets)} | Use page parameter to navigate")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ticketcmd(bot))
