import discord
from discord.ext import commands
from discord import app_commands

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
                view = TicketButtons(interaction.user, subject, description)
                await ticket_channel.send(embed=embed, view=view)
                await interaction.response.send_message("Your ticket has been submitted!", ephemeral=True, delete_after=8)
            else:
                await interaction.response.send_message("Ticket channel not found. Please contact an administrator.",
                                                        ephemeral=True, delete_after=8)
        else:
            await interaction.response.send_message("Tickets have to be sent in a guild, silly! :3 /setup for more info",
                                                    ephemeral=True, delete_after=8)

class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user: discord.User, subject: str, description: str):
        super().__init__(timeout=None)
        self.ticket_user = ticket_user
        self.subject = subject
        self.description = description

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.ticket_user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        support_role = discord.utils.get(guild.roles, name=".trusted")  
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True)
        category = await guild.create_category(
            name=f"Ticket-{self.ticket_user.name}",
            overwrites=overwrites,
            reason="New ticket accepted"
        )
        await category.edit(position=len(guild.categories))  
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{self.ticket_user.name}",
            topic=f"Support ticket for {self.ticket_user.name}",
            reason="New ticket accepted"
        )
        embed = discord.Embed(title="Ticket Details", color=discord.Color.dark_grey())
        embed.add_field(name="Subject", value=self.subject, inline=False)
        embed.add_field(name="Description", value=self.description, inline=False)
        embed.add_field(name="Submitted by", value=self.ticket_user.name, inline=False)
        close_view = CloseTicketButton(self.ticket_user)  
        await ticket_channel.send(
            content=f"Hello {self.ticket_user.mention}, a support member will be with you shortly.",
            embed=embed, view=close_view)
        await interaction.response.send_message(f"Ticket accepted and channel created: {ticket_channel.mention}",
                                                ephemeral=True, delete_after=8)
        await interaction.message.delete()
        await self.ticket_user.send(f"Ticket accepted {ticket_channel.mention} by {interaction.user.name}.")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            await self.ticket_user.send(f"Your ticket has been rejected by {interaction.user.name}.")
            await interaction.message.delete()
        else:
            await interaction.response.send_message("You do not have permission to reject this ticket.", ephemeral=True, delete_after=8)

class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_user: discord.User):
        super().__init__(timeout=None)
        self.ticket_user = ticket_user

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        trusted_role = discord.utils.get(interaction.guild.roles, name=".trusted")
        if trusted_role in interaction.user.roles:
            await self.ticket_user.send(f"Your ticket has been closed by {interaction.user.name}.")
            await interaction.channel.delete(reason="Ticket closed by support staff")
            category = interaction.channel.category
            if category and len(category.channels) == 0:
                await category.delete(reason="Category empty after ticket closed")
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True, delete_after=8)

class ticketcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Submit a support ticket")
    async def ticket_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal())

async def setup(bot):
    await bot.add_cog(ticketcmd(bot))
    print("✓ Ticket command loaded successfully")
