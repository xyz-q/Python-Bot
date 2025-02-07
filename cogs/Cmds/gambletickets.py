import json
import datetime
import discord
from discord.ext import commands
from pathlib import Path
from discord.ui import Button, View
import asyncio
from discord.ui import Modal, TextInput
import typing
import os
from cogs.Cmds.gamble import has_account
import asyncio
import asyncio

class ConfirmView(View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

    async def on_timeout(self):
        self.value = None
        self.stop()

class TicketView(discord.ui.View):
    def __init__(self, bot, cog, user, command_message):
        super().__init__(timeout=90)
        self.bot = bot
        self.cog = cog
        self.user = user
        self.command_message = command_message
        self.page = 0
        self.is_admin = str(user.id) in map(str, cog.admin_ids)
        self.current_view = "main"
        self.message = None

        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Admin View":
                child.disabled = not self.is_admin
                child.style = discord.ButtonStyle.grey if not self.is_admin else discord.ButtonStyle.green
        
        self.previous_button.disabled = True
        self.next_button.disabled = True
        self.previous_button.style = discord.ButtonStyle.gray
        self.next_button.style = discord.ButtonStyle.gray

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

            
        if self.message:
            embed = self.message.embeds[0]
            embed.color = discord.Color.red()
            embed.description = "❌ This menu has timed out."
            
            try:
                await self.message.edit(embed=embed, view=self)
            except:
                pass

    def get_max_pages(self):
        if self.current_view == "admin":
            all_tickets = []
            for t_type in ["deposit", "withdraw"]:
                for ticket_id, ticket in self.cog.tickets[t_type].items():
                    all_tickets.append((t_type, ticket_id, ticket))
            return max(0, len(all_tickets) - 1)
        else:
            user_tickets = []
            for t_type in ["deposit", "withdraw"]:
                for ticket_id, ticket in self.cog.tickets[t_type].items():
                    if str(ticket['user_id']) == str(self.user.id):
                        user_tickets.append((t_type, ticket_id, ticket))
            return max(0, len(user_tickets) - 1)

    def update_button_visibility(self):
        max_pages = self.get_max_pages()
        
        if self.current_view == "main":
            self.list_button.label = "List Tickets"
            self.list_button.emoji = "📋"
            self.admin_view_button.label = "Admin View"
            self.admin_view_button.emoji = "🔧"
            self.show_navigation(False)
            self.list_button.disabled = False
            self.admin_view_button.disabled = False
        elif self.current_view == "list":
            self.list_button.label = "Main"
            self.list_button.emoji = "🏠"
            self.show_navigation(True)
            self.list_button.disabled = False
            self.admin_view_button.disabled = True
            
            if self.page <= 0:
                self.previous_button.disabled = True
                self.previous_button.style = discord.ButtonStyle.grey
            else:
                self.previous_button.disabled = False
                self.previous_button.style = discord.ButtonStyle.blurple

            if self.page >= max_pages:
                self.next_button.disabled = True
                self.next_button.style = discord.ButtonStyle.grey
            else:
                self.next_button.disabled = False
                self.next_button.style = discord.ButtonStyle.blurple

        elif self.current_view == "admin":
            self.admin_view_button.label = "Main"
            self.admin_view_button.emoji = "🏠"
            self.show_navigation(True)
            self.list_button.disabled = True
            self.admin_view_button.disabled = False
            
            if self.page <= 0:
                self.previous_button.disabled = True
                self.previous_button.style = discord.ButtonStyle.grey
            else:
                self.previous_button.disabled = False
                self.previous_button.style = discord.ButtonStyle.blurple

            if self.page >= max_pages:
                self.next_button.disabled = True
                self.next_button.style = discord.ButtonStyle.grey
            else:
                self.next_button.disabled = False
                self.next_button.style = discord.ButtonStyle.blurple

    def get_user_ticket_counts(self):
        deposit_count = 0
        withdraw_count = 0
        for ticket_id, ticket in self.cog.tickets['deposit'].items():
            if str(ticket['user_id']) == str(self.user.id):
                deposit_count += 1
        for ticket_id, ticket in self.cog.tickets['withdraw'].items():
            if str(ticket['user_id']) == str(self.user.id):
                withdraw_count += 1
        return deposit_count, withdraw_count

    def get_total_ticket_counts(self):
        return len(self.cog.tickets['deposit']), len(self.cog.tickets['withdraw'])

    def create_embed(self):
        deposit_count, withdraw_count = self.get_user_ticket_counts()
        total_deposits, total_withdraws = self.get_total_ticket_counts()

        embed = discord.Embed(
            title="🎫 Ticket System",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Your Active Tickets",
            value=f"```\n"
                  f"Deposit Tickets:  {deposit_count}\n"
                  f"Withdraw Tickets: {withdraw_count}\n"
                  f"Total Tickets:    {deposit_count + withdraw_count}\n"
                  f"```",
            inline=False
        )

        if self.is_admin:
            embed.add_field(
                name="System Overview",
                value=f"```\n"
                      f"Total Deposits:    {total_deposits}\n"
                      f"Total Withdraws:   {total_withdraws}\n"
                      f"Total Tickets:     {total_deposits + total_withdraws}\n"
                      f"```",
                inline=False
            )

        embed.add_field(
            name="Quick Actions",
            value="• Use `List Tickets` to view your active tickets\n"

                  + ("• Use `Admin View` to see all system tickets\n" if self.is_admin else ""),
            inline=False
        )

        return embed

    async def update_view(self):
        """Update the view after ticket changes"""
        if self.current_view == "admin":
            embed = self.create_admin_embed()
        else:
            embed = self.create_list_embed()
        
        max_pages = self.get_max_pages()
        if self.page > max_pages:
            self.page = max_pages

        if self.message:
            await self.message.edit(embed=embed, view=self)

    def create_list_embed(self):
        user_tickets = []
        for t_type in ["deposit", "withdraw"]:
            for ticket_id, ticket in self.cog.tickets[t_type].items():
                if str(ticket['user_id']) == str(self.user.id):
                    user_tickets.append((t_type, ticket_id, ticket))

        if not user_tickets:
            embed = discord.Embed(
                title="🎫 Your Tickets",
                description="You have no pending tickets!",
                color=discord.Color.gold()
            )
            return embed

        current_ticket = user_tickets[self.page]
        t_type, ticket_id, ticket = current_ticket
        
        embed = discord.Embed(
            title="🎫 Your Tickets",
            description=f"Showing ticket {self.page + 1} of {len(user_tickets)}",
            color=discord.Color.gold()
        )

        embed.add_field(
            name=f"{t_type.title()} Ticket #{ticket_id}",
            value=f"**Amount**\n<:goldpoints:1319902464115343473> {self.cog.format_amount2(ticket['amount'])}\n\n"
                f"**RSN**\n{ticket['rsn']}\n\n"
                f"**Date**\n{ticket['date']}",
            inline=False
        )
        quick_actions = f"<:remove:1328511957208268800> `,ticket cancel {ticket_id} <reason>`"
        embed.add_field(name="Quick Actions", value=quick_actions, inline=False)

        embed.set_footer(text=f"Use arrow buttons to navigate")
        return embed

    def create_admin_embed(self):
        tickets_list = []
        for t_type in ["deposit", "withdraw"]:
            for ticket_id, ticket in self.cog.tickets[t_type].items():
                tickets_list.append((t_type, ticket_id, ticket))

        if not tickets_list:
            embed = discord.Embed(
                title="🎫 Pending Tickets",
                description="No pending tickets found!",
                color=discord.Color.gold()
            )
            return embed

        current_ticket = tickets_list[self.page]
        t_type, ticket_id, ticket = current_ticket
        
        embed = discord.Embed(
            title="🎫 Pending Tickets",
            description=f"Showing ticket {self.page + 1} of {len(tickets_list)}",
            color=discord.Color.gold()
        )

        embed.add_field(
            name=f"{t_type.title()} Ticket #{ticket_id}",
            value=f"**User**\n{ticket['user_name']}\n\n"
                f"**Amount**\n<:goldpoints:1319902464115343473> {self.cog.format_amount2(ticket['amount'])}\n\n"
                f"**RSN**\n{ticket['rsn']}\n\n"
                f"**Date**\n{ticket['date']}",
            inline=False
        )
        quick_actions = f"<:add:1328511998647861390> `,ticket accept {ticket_id}`\n<:remove:1328511957208268800> `,ticket decline {ticket_id}`"
        embed.add_field(name="Quick Actions", value=quick_actions, inline=False)

        embed.set_footer(text=f"Use arrow buttons to navigate")
        return embed
    
    def show_navigation(self, show: bool):
        self.previous_button.disabled = not show
        self.next_button.disabled = not show
        if show:
            self.previous_button.style = discord.ButtonStyle.blurple
            self.next_button.style = discord.ButtonStyle.blurple
        else:
            self.previous_button.style = discord.ButtonStyle.grey
            self.next_button.style = discord.ButtonStyle.grey

    @discord.ui.button(label="List Tickets", style=discord.ButtonStyle.blurple, emoji="📋")
    async def list_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_view == "main":
            self.current_view = "list"
            embed = self.create_list_embed()
        else:
            self.current_view = "main"
            embed = self.create_embed()
        
        self.update_button_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey, emoji="⬅️", row=1)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        embed = self.create_admin_embed() if self.current_view == "admin" else self.create_list_embed()
        self.update_button_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey, emoji="➡️", row=1)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        embed = self.create_admin_embed() if self.current_view == "admin" else self.create_list_embed()
        self.update_button_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Admin View", style=discord.ButtonStyle.green, emoji="🔧")
    async def admin_view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_view == "main":
            self.current_view = "admin"
            embed = self.create_admin_embed()
        else:
            self.current_view = "main"
            embed = self.create_embed()
        
        self.update_button_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close Menu", style=discord.ButtonStyle.red, row=2)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id"):
            if interaction.data["custom_id"] == "list_button" and self.list_button.label == "Main":
                await self.return_to_main(interaction, "list")
                return False
            elif interaction.data["custom_id"] == "admin_view_button" and self.admin_view_button.label == "Main":
                await self.return_to_main(interaction, "admin")
                return False
        return True


class CancelTicketModal(discord.ui.Modal, title="Cancel Ticket"):
    def __init__(self, cog, view):
        super().__init__()
        self.cog = cog
        self.view = view

        self.ticket_id = discord.ui.TextInput(
            label="Ticket ID",
            placeholder="Enter the ticket ID to cancel",
            required=True,
            min_length=1,
            max_length=10
        )
        self.add_item(self.ticket_id)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_id = self.ticket_id.value
        found = False

        for t_type in ["deposit", "withdraw"]:
            if ticket_id in self.cog.tickets[t_type]:
                ticket = self.cog.tickets[t_type][ticket_id]
                if str(ticket['user_id']) == str(interaction.user.id):
                    del self.cog.tickets[t_type][ticket_id]
                    self.cog.save_tickets()
                    found = True
                    break

        if found:
            embed = self.view.create_embed()
            await interaction.response.edit_message(embed=embed, view=self.view)
            await interaction.followup.send(f"✅ Ticket {ticket_id} has been cancelled!", ephemeral=True, delete_after=8)
        else:
            await interaction.response.send_message("❌ Invalid ticket ID or you don't own this ticket!", ephemeral=True, delete_after=8)

class AdminTicketView(View):
    def __init__(self, bot, user_id, timer_msg, ticket_data, public_msg, cog, ticket_type, user_timer, dm_timer, user_embed, admin_embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.timer_msg = timer_msg
        self.ticket_data = ticket_data
        self.public_msg = public_msg
        self.cog = cog
        self.ticket_type = ticket_type
        self.user_timer = user_timer
        self.dm_timer = dm_timer
        self.user_embed = user_embed
        self.admin_embed = admin_embed

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.green)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.bot.get_user(int(self.user_id))
        if str(self.user_id) in self.cog.active_sessions:
            del self.cog.active_sessions[str(self.user_id)]
            print("Deleted active session")
        
        timer_id = f"{interaction.user.id}_{self.user_id}"
        self.cog.active_timers[timer_id] = False        
        
        if user:
            await self.user_timer.edit(content=f"<:add:1328511998647861390> {self.ticket_type.capitalize()} completed! Thank you for using our services!")
            await asyncio.sleep(2)
            await user.send("<:add:1328511998647861390> Your ticket has been closed.")
            await self.user_embed.delete()
        
        await self.public_msg.delete()
        await self.timer_msg.delete()
        
        await self.admin_embed.delete()
        await self.dm_timer.edit(content=f"<:add:1328511998647861390> {self.ticket_type.capitalize()} completed! Amount: {self.cog.format_amount2(self.ticket_data['amount'])} <:goldpoints:1319902464115343473>")




        if self.ticket_data['ticket_id'] in self.cog.tickets[self.ticket_type]:
            del self.cog.tickets[self.ticket_type][self.ticket_data['ticket_id']]
            self.cog.save_tickets()
        
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.bot.get_user(int(self.user_id))
        if str(self.user_id) in self.cog.active_sessions:
            del self.cog.active_sessions[str(self.user_id)]
            print("Deleted active session")
        
        timer_id = f"{interaction.user.id}_{self.user_id}"
        self.cog.active_timers[timer_id] = False
        
        if user:
            await self.user_timer.edit(content="<:remove:1328511957208268800> Trade cancelled by the admin.")
            await asyncio.sleep(2)
            await user.send("<:remove:1328511957208268800> Your ticket has been closed.")
            await self.user_embed.delete()
        
        await self.public_msg.delete()
        await self.timer_msg.delete()
        
        await self.admin_embed.delete()
        await self.dm_timer.edit(content="<:remove:1328511957208268800> Trade cancelled!")

        if self.ticket_data['ticket_id'] in self.cog.tickets[self.ticket_type]:
            del self.cog.tickets[self.ticket_type][self.ticket_data['ticket_id']]
            self.cog.save_tickets()
        
        self.stop()








class TicketPaginationView(View):
    def __init__(self, tickets_list, cog, timeout=20):
        super().__init__(timeout=timeout)
        self.tickets_list = tickets_list
        self.current_page = 0
        self.total_pages = len(tickets_list)
        self.message = None
        self.cog = cog
        self.first_page = Button(label="⏮", custom_id="first", style=discord.ButtonStyle.grey)
        self.prev_page = Button(label="◀", custom_id="previous", style=discord.ButtonStyle.primary)
        self.next_page = Button(label="▶", custom_id="next", style=discord.ButtonStyle.primary)
        self.last_page = Button(label="⏭", custom_id="last", style=discord.ButtonStyle.grey)
        
        self.close_button = Button(
            label="✖", 
            custom_id="close", 
            style=discord.ButtonStyle.danger,
            row=1
        )
        
        self.add_item(self.first_page)
        self.add_item(self.prev_page)
        self.add_item(self.next_page)
        self.add_item(self.last_page)
        self.add_item(self.close_button)
        
        self.update_buttons()
        
    def update_buttons(self):
        """Update button states based on current page"""
        self.first_page.disabled = self.current_page == 0
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == self.total_pages - 1
        self.last_page.disabled = self.current_page == self.total_pages - 1
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "close":
            await interaction.message.delete()
            return True

        button_actions = {
            "first": lambda: setattr(self, 'current_page', 0),
            "previous": lambda: setattr(self, 'current_page', max(0, self.current_page - 1)),
            "next": lambda: setattr(self, 'current_page', min(self.total_pages - 1, self.current_page + 1)),
            "last": lambda: setattr(self, 'current_page', self.total_pages - 1)
        }
        
        action = button_actions.get(interaction.data["custom_id"])
        if action:
            action()
            self.update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        
        return True
    
    def create_embed(self):
        ticket_type, ticket_id, ticket = self.tickets_list[self.current_page]
        
        embed = discord.Embed(
            title="🎫 Pending Tickets",
            description=f"Showing ticket {self.current_page + 1} of {self.total_pages}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name=f"{ticket_type.title()} Ticket #{ticket_id}",
            value=f"**User**\n{ticket['user_name']}\n\n"
                f"**Amount**\n<:goldpoints:1319902464115343473> {self.cog.format_amount2(ticket['amount'])}\n\n"
                f"**RSN**\n{ticket['rsn']}\n\n"
                f"**Date**\n{ticket['date']}",
            inline=False
        )
        
        quick_actions = f"<:add:1328511998647861390> `,ticket accept {ticket_id}`\n<:remove:1328511957208268800> `,ticket decline {ticket_id}`"
        embed.add_field(name="Quick Actions", value=quick_actions, inline=False)
        
        embed.set_footer(text=f"Ticket ID: #{ticket_id} • Use arrow buttons to navigate")
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        try:
            if self.message:
                await self.message.delete()
        except:
            pass  

class GambleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_ids = [110927272210354176]  
        self.tickets_file = ".json/tickets.json"
        self.load_tickets()
        self.message = None
        self.active_timers = {}
        self.currency = {}
        self.currency_file = ".json/currency.json" 
        self.load_currency()
        self.MIN_DEPOSIT = 5_000_000  
        self.MAX_DEPOSIT = 750_000_000  
        self.MIN_WITHDRAW = 10_000_000  
        self.MAX_WITHDRAW = 250_000_000
        self.USER_ID_LIMIT = 1_000_000_000_000
        self.active_sessions = {}
        self.active_views = set()


    def is_house_name(self, name: str) -> bool:
        """Check if a name contains 'house' (case-insensitive)"""
        return 'house' in str(name).lower()

    async def validate_user(self, user: typing.Union[discord.Member, str]) -> tuple[str, str, bool]:
        """
        Validates a user input and returns (user_id, display_name, is_valid)
        """
        try:
            if isinstance(user, str) and user.lower().strip() == "house":
                return str(self.bot.user.id), "🏦 House", True
            
            if isinstance(user, discord.Member):
                return str(user.id), user.name, True
            
            return None, None, False
        except Exception as e:
            print(f"Error in validate_user: {e}")
            return None, None, False
        
    def load_currency(self):
        """Load currency data from JSON file"""
        try:
            if os.path.exists(self.currency_file):
                with open(self.currency_file, 'r') as f:
                    self.currency = json.load(f)
                    
            else:
                print(f"Currency file not found at {self.currency_file}")
        except Exception as e:
            print(f"Error loading currency file: {e}")
            self.currency = {}

    async def get_balance(self, user_id) -> int:
        """Get balance for any user or house"""
        try:
            str_user_id = str(user_id)
            
            if str_user_id == "HOUSE" or str_user_id == "house":
                str_user_id = "1233966655923552370"
            
            return int(self.currency.get(str_user_id, 0))
            
        except Exception as e:
            print(f"Error in get_balance for user_id {user_id}: {e}")
            return 0

    def parse_amount(self, amount_str):
        try:
            amount_str = str(amount_str).replace(',', '').upper().strip()
            
            multipliers = {
                'K': 1000,
                'M': 1000000,
                'B': 1000000000,
                'T': 1000000000000
            }
            
            number = ''
            multiplier = ''
            
            for char in amount_str:
                if char.isdigit() or char == '.':
                    number += char
                elif char in multipliers:
                    multiplier = char
                    break
            
            if not number:
                return None
                
            amount = float(number)
            
            if multiplier in multipliers:
                amount *= multipliers[multiplier]
                
            return int(amount)
            
        except (ValueError, TypeError):
            return None

    def format_amount2(self, amount):
        if amount >= 1000000000000:
            if amount >= 10000000000000:
                trillions = amount / 1000000000000
                return f"{int(trillions):,}T"
            else:
                billions = amount / 1000000000
                return f"{int(billions):,}B"
                
        elif amount >= 1000000000:
            if amount >= 10000000000:
                billions = amount / 1000000000
                return f"{int(billions):,}B"
            else:
                millions = amount / 1000000
                return f"{int(millions):,}M"
                
        elif amount >= 1000000:
            if amount >= 10000000:
                millions = amount / 1000000
                return f"{int(millions):,}M"
            else:
                thousands = amount / 1000
                return f"{int(thousands):,}K"
                
        elif amount >= 1000:
            thousands = amount / 1000
            return f"{int(thousands):,}K"
        
        return f"{int(amount):,}"


    async def update_timer_message(self, message, end_time, user_id, customer_id, dm_message=None, public_msg=None, user_msg=None, admin_msg=None, user_embed_msg=None, admin_embed_msg=None, ticket_id=None, ticket_type=None):
        try:
            timer_id = f"{user_id}_{customer_id}"
            self.active_timers[timer_id] = True

            user = self.bot.get_user(int(customer_id))
            
            while self.active_timers.get(timer_id, False):
                now = datetime.datetime.now()
                time_left = end_time - now
                
                if time_left.total_seconds() <= 0:
                    if user:
                        await user_msg.edit(content=f"<:remove:1328511957208268800> Trade ID: {ticket_id} cancelled - Time expired!")
                        if user_embed_msg:
                            await user_embed_msg.delete()

                    if public_msg:
                        await public_msg.delete()
                    if message:
                        await message.delete()

                    if admin_embed_msg:
                        await admin_embed_msg.delete()
                    if dm_message:
                        await dm_message.edit(content=f"<:remove:1328511957208268800> Trade ID: {ticket_id} cancelled - Time expired!")

                    if ticket_id in self.tickets[ticket_type]:
                        del self.tickets[ticket_type][ticket_id]
                        self.save_tickets()

                    if str(customer_id) in self.active_sessions:
                        session = self.active_sessions[str(customer_id)]
                        admin = self.bot.get_user(int(session['admin_id']))
                        
                        if user:
                            try:
                                await user.send("<:remove:1328511957208268800> This ticket session has ended due to timer expiration. Please make a new one.")
                            except:
                                pass
                        
                        if admin:
                            try:
                                await admin.send(f"<:remove:1328511957208268800> Session for ticket #{ticket_id} has ended due to timer expiration.")
                            except:
                                pass
                                
                        del self.active_sessions[str(customer_id)]
                        print(f"Deleted active session for user {customer_id} due to timer expiration")

                    if timer_id in self.active_timers:
                        del self.active_timers[timer_id]
                        print(f"Deleted active timer {timer_id} due to expiration")

                    break

                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                
                timer_text = f"⏳ Time remaining: {minutes}m {seconds}s"
                
                if user_msg:
                    try:
                        await user_msg.edit(content=timer_text)
                    except:
                        pass
                
                if dm_message:
                    try:
                        await dm_message.edit(content=timer_text)
                    except:
                        pass
                
                await asyncio.sleep(13)

            if timer_id in self.active_timers:
                del self.active_timers[timer_id]

        except Exception as e:
            print(f"Error in update_timer_message: {e}")
            try:
                if str(customer_id) in self.active_sessions:
                    del self.active_sessions[str(customer_id)]
                if timer_id in self.active_timers:
                    del self.active_timers[timer_id]
            except:
                pass





    def load_tickets(self):
        try:
            with open(self.tickets_file, 'r') as f:
                data = json.load(f)
                self.tickets = data.get("tickets", {"deposit": {}, "withdraw": {}})
                self.last_ticket_id = data.get("last_ticket_id", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tickets = {"deposit": {}, "withdraw": {}}
            self.last_ticket_id = 0
            self.save_tickets()

    async def save_tickets(self):
        data = {
            "tickets": self.tickets,
            "last_ticket_id": self.last_ticket_id
        }
        with open(self.tickets_file, 'w') as f:
            json.dump(data, f, indent=4)



    @commands.group(invoke_without_command=True, aliases=["tickets"])
    async def ticket(self, ctx):
        await ctx.message.delete()
        """View and manage your tickets"""
        view = TicketView(self.bot, self, ctx.author, ctx.message)
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)
        self.active_views.add(view)

        await view.wait()
        self.active_views.discard(view)
        await asyncio.sleep(5)
        await view.message.delete()
        



    @ticket.command(name="list")
    async def ticket_list(self, ctx, type=None):
        await ctx.message.delete()
        """List your pending tickets"""
        if type and type not in ["deposit", "withdraw"]:
            await ctx.send("<:remove:1328511957208268800> Invalid type! Use 'deposit' or 'withdraw'")
            return

        tickets_list = []
        types_to_show = [type] if type else ["deposit", "withdraw"]
        
        for t in types_to_show:
            for ticket_id, ticket in self.tickets[t].items():
                if str(ticket['user_id']) == str(ctx.author.id):
                    tickets_list.append((t, ticket_id, ticket))

        if not tickets_list:
            await ctx.send("<:remove:1328511957208268800> You have no pending tickets!")
            return

        view = TicketPaginationView(tickets_list, self)
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)

    @ticket.command(name="admin")
    async def admin_list(self, ctx, type=None):
        await ctx.message.delete()
        """List all pending tickets"""
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("<:remove:1328511957208268800> You don't have permission to use this command!")
            return

        if type and type not in ["deposit", "withdraw"]:
            await ctx.send("<:remove:1328511957208268800> Invalid type! Use 'deposit' or 'withdraw'")
            return

        tickets_list = []
        types_to_show = [type] if type else ["deposit", "withdraw"]
        
        for t in types_to_show:
            for ticket_id, ticket in self.tickets[t].items():
                tickets_list.append((t, ticket_id, ticket))

        if not tickets_list:
            await ctx.send("<:remove:1328511957208268800> No pending tickets found!")
            return

        view = TicketPaginationView(tickets_list, self)
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)


    @ticket.command(name="accept")
    async def accept_ticket(self, ctx, ticket_id: str):
        """Accept a ticket"""
        await ctx.message.delete()
        
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("<:remove:1328511957208268800> You don't have permission to use this command!")
            return

        ticket_type = None
        ticket_data = None
        for type in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[type]:
                ticket_type = type
                ticket_data = self.tickets[type][ticket_id]
                break

        if not ticket_data:
            await ctx.send("<:remove:1328511957208268800> Invalid ticket ID!")
            return

        user = self.bot.get_user(int(ticket_data['user_id']))
        ticket_data['ticket_id'] = ticket_id

        question_msg = await ctx.send("Please enter your __***RSN***__:")

        messages_to_delete = []

        try:
            while True:
                rsn_response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                )
                
                await rsn_response.delete()
                admin_rsn = str(rsn_response.content)

                await question_msg.edit(content="Please enter your __***combat***__ __***level***__:")
                level_response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                )
                await level_response.delete()
                admin_level = level_response.content
                
                await question_msg.edit(content="Please enter the __***world***__:")
                world_response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                )
                await world_response.delete()
                world = world_response.content

                await question_msg.edit(content="Please enter the __***location***__:")
                location_response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                )
                await location_response.delete()
                location = location_response.content.title()

                await question_msg.delete()
                await asyncio.sleep(0.5)

                summary1 = await ctx.send(f"RSN: {admin_rsn}")
                await asyncio.sleep(0.5)
                summary2 = await ctx.send(f"Combat Level: {admin_level}")
                await asyncio.sleep(0.5)
                summary3 = await ctx.send(f"World: {world}")
                await asyncio.sleep(0.5)
                summary4 = await ctx.send(f"Location: {location}")
                await asyncio.sleep(2)
                confirm_msg = await ctx.send("'__**confirm**__' to submit or '__**decline**__' to cancel")

                while True:
                    confirmation = await self.bot.wait_for(
                        'message',
                        timeout=30.0,
                        check=lambda message: message.author == ctx.author and message.channel == ctx.channel
                    )
                    await confirmation.delete()
                    
                    if confirmation.content.lower() in ['confirm', 'decline']:
                        await confirm_msg.delete()
                        await summary1.delete()
                        await summary2.delete()
                        await summary3.delete()
                        await summary4.delete()

                        if confirmation.content.lower() == 'decline':
                            await ctx.send("Information declined and discarded.")
                            return
                        
                        if confirmation.content.lower() == 'confirm':
                            user_embed = discord.Embed(
                                title=f"<:add:1328511998647861390> Active {ticket_type} \n       ",
                                description=f"Your {ticket_type} request has been approved.\n\n__***We will never trade you first.***__\n\n__***Please confirm it's you before trading.***__\n\n__***You can message the bot to talk with an admin.***__\n\n ",
                                color=discord.Color.gold()
                            )
                            user_embed.add_field(
                                name="Admin Details",
                                value=f"RSN: {admin_rsn}\nCombat Level: {admin_level}",
                                inline=False
                            )
                            user_embed.add_field(
                                name="Meeting Point",
                                value=f"World {world}\nLocation: {location}",
                                inline=False
                            )
                            user_embed.add_field(
                                name="Amount",
                                value=f"{self.format_amount2(ticket_data['amount'])} <:goldpoints:1319902464115343473>",
                                inline=False
                            )
                            user_embed.add_field(
                                name="Client RSN",
                                value=ticket_data['rsn'],
                                inline=False
                            )
                            user_embed.set_footer(text=f"Approved by {ctx.author}")
                            
                            admin_embed = user_embed.copy()
                            admin_embed.title = f"🎫 Active {ticket_type} "
                            admin_embed.description = f"Ticket ID: {ticket_id} for {ticket_data['user_name']}"
                            
                            if user:
                                user_embed_msg = await user.send(embed=user_embed)
                                user_timer_msg = await user.send("⏳ Time remaining: 10m 0s")
                            
                            public_msg = await ctx.send("<:add:1328511998647861390> Trade session started.")
                            timer_msg = await ctx.send(f"Ticket #{ticket_id} accepted by {ctx.author}.")
                            
                            admin_embed_msg = await ctx.author.send(embed=admin_embed)
                            admin_timer_msg = await ctx.author.send("⏳ Time remaining: 10m 0s")
                            
                            admin_view = AdminTicketView(
                                self.bot, 
                                ticket_data['user_id'], 
                                timer_msg, 
                                ticket_data, 
                                public_msg, 
                                self, 
                                ticket_type,
                                user_timer_msg,
                                admin_timer_msg,
                                user_embed_msg,
                                admin_embed_msg
                            )
                            await admin_embed_msg.edit(view=admin_view)
                            self.active_sessions[str(ticket_data['user_id'])] = {
                                'admin_id': str(ctx.author.id),
                                'ticket_id': ticket_id
                            }                
                            end_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            await self.update_timer_message(
                                timer_msg, 
                                end_time,
                                ctx.author.id,
                                ticket_data['user_id'],
                                admin_timer_msg,
                                public_msg,
                                user_timer_msg,
                                admin_embed_msg,
                                user_embed_msg,
                                admin_embed_msg,
                                ticket_id,
                                ticket_type
                            )
                            return
                        break
                    else:
                        error_msg = await ctx.send("<:remove:1328511957208268800> Please type 'confirm' or 'decline'", delete_after=2)

        except asyncio.TimeoutError:
            try:
                await ctx.channel.delete_messages(messages_to_delete)
            except:
                for msg in messages_to_delete:
                    try:
                        await msg.delete()
                    except:
                        pass
            await ctx.send("<:remove:1328511957208268800> Confirmation timed out. Please try again.", delete_after=5)
            return

        except asyncio.TimeoutError:
            await question_msg.delete()
            await ctx.send("<:remove:1328511957208268800> Timed out waiting for response.", delete_after=5)
            return






    @ticket.command(name="decline")
    async def decline_ticket(self, ctx, ticket_id: str, *, reason: str):
        await ctx.message.delete()
        """Decline a ticket with a reason"""
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("<:remove:1328511957208268800> You don't have permission to use this command!")
            return

        ticket_type = None
        ticket_data = None
        for type in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[type]:
                ticket_type = type
                ticket_data = self.tickets[type][ticket_id]
                break

        if not ticket_data:
            await ctx.send("<:remove:1328511957208268800> Invalid ticket ID!")
            return

        user = self.bot.get_user(int(ticket_data['user_id']))
        
        if user:
            embed = discord.Embed(
                title="<:remove:1328511957208268800> Request Declined",
                description=f"Your {ticket_type} request has been declined.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Amount",
                value=f"<:goldpoints:1319902464115343473> {ticket_data['amount']}",
                inline=False
            )
            embed.add_field(
                name="RSN",
                value=ticket_data['rsn'],
                inline=False
            )
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            embed.set_footer(text=f"Declined by {ctx.author}")
            await user.send(embed=embed)

        del self.tickets[ticket_type][ticket_id]
        await self.save_tickets()
        declinemsg = await ctx.send(f"<:add:1328511998647861390> Ticket #{ticket_id} has been declined! Reason: {reason}")
        await asyncio.sleep(7)
        await declinemsg.delete()

        for view in self.active_views.copy():
            try:
                await view.update_view()
            except Exception as e:
                print(f"Failed to update view: {e}")
                self.active_views.discard(view)
                
    @ticket.command(name="cancel")
    async def Cancel(self, ctx, ticket_id, *, reason=None):
        await ctx.message.delete()
        if not reason:
            return await ctx.send(f"<:remove:1328511957208268800> Please provide a reason for cancellation!\nUsage: `!ticket cancel <ticket_id> <reason>`")

        found = False
        ticket_type = None
        ticket = None
        
        for t in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[t]:
                found = True
                ticket_type = t
                ticket = self.tickets[t][ticket_id]
                break
        
        if not found:
            return await ctx.send(f"<:remove:1328511957208268800> Invalid ticket ID!")
        
        if ticket["user_id"] != str(ctx.author.id):
            return await ctx.send("You can only cancel your own tickets!")
        
        del self.tickets[ticket_type][ticket_id]
        self.save_tickets()
        
        for view in self.active_views.copy():
            try:
                await view.update_view()
            except Exception as e:
                print(f"Failed to update view: {e}")
                self.active_views.discard(view)        

        cancelmsg = await ctx.send(f"<:add:1328511998647861390> Ticket `{ticket_id}` has been cancelled!\nReason: {reason}")
        await asyncio.sleep(7)
        await cancelmsg.delete()
        
        for admin_id in self.admin_ids:
            try:
                admin = await self.bot.fetch_user(admin_id)
                embed = discord.Embed(
                    title="<:remove:1328511957208268800> Ticket Cancelled",
                    color=discord.Color.red(),
                    timestamp=ctx.message.created_at
                )
                embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
                embed.add_field(name="Type", value=ticket_type.capitalize(), inline=True)
                embed.add_field(name="User", value=f"{ticket['user_name']}", inline=True)
                embed.add_field(name="Amount", value=f" <:goldpoints:1319902464115343473> {ticket['amount']:,}", inline=True)
                embed.add_field(name="RSN", value=ticket['rsn'], inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                
                await admin.send(embed=embed)
                for view in self.active_views:
                    await view.update_view()                
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")




    def generate_ticket_id(self):
        self.last_ticket_id += 1
        return str(self.last_ticket_id)    
    

    
    @has_account()                  
    @commands.command()                  
    async def deposit(self, ctx, amount=None, *, rsn=None):
        """Create a deposit request"""
        if not amount or not rsn:
            await ctx.send("<:remove:1328511957208268800> Please use the correct format\nExample: `,deposit 100M Zezima`")
            return
        
        formatted_amount = self.parse_amount(amount)
        if not formatted_amount:
            await ctx.send("<:remove:1328511957208268800> Invalid amount format! Please use K, M, B, or T (e.g., 100M, 1B)")
            return

        confirm_embed = discord.Embed(
            title="📝 Confirm Deposit Request",
            description="Please verify the following details are correct:",
            color=discord.Color.gold()
        )
        confirm_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
            inline=False
        )
        confirm_embed.add_field(
            name="RSN",
            value=rsn,
            inline=False
        )
        
        view = ConfirmView(timeout=30)
        confirm_msg = await ctx.send(embed=confirm_embed, view=view)
        
        try:
            await ctx.message.delete()
        except:
            pass

        await view.wait()
        
        if view.value is None:
            await confirm_msg.edit(content="<:remove:1328511957208268800> Confirmation timed out. Please try again.", embed=None, view=None)
            return
        
        if view.value is False:
            await confirm_msg.edit(content="<:remove:1328511957208268800> Deposit request cancelled.", embed=None, view=None)
            return
        
        await confirm_msg.delete()
                    
        ticket_id = self.generate_ticket_id()
        ticket_data = {
            "user_id": str(ctx.author.id),
            "user_name": str(ctx.author),
            "amount": formatted_amount,
            "rsn": rsn,
            "date": discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        self.tickets["deposit"][ticket_id] = ticket_data
        self.save_tickets()

        user_embed = discord.Embed(
            title="<:add:1328511998647861390> Deposit Request Sent",
            description="Your deposit request has been sent to an administrator.",
            color=discord.Color.green()
        )
        user_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
            inline=False
        )
        user_embed.add_field(
            name="RSN",
            value=rsn,
            inline=False
        )
        user_embed.add_field(
            name="Ticket ID",
            value=f"#{ticket_id}",
            inline=False
        )
        user_embed.set_footer(text="Please wait for an administrator to process your request.")
        await ctx.send(embed=user_embed)

        for admin_id in self.admin_ids:
            admin = self.bot.get_user(admin_id)
            if admin:
                admin_embed = discord.Embed(
                    title="<:add:1328511998647861390> New Deposit Request",
                    description=f" A new deposit request has been submitted.",
                    color=discord.Color.green()
                )
                admin_embed.add_field(
                    name="User",
                    value=ctx.author.mention,
                    inline=False
                )
                admin_embed.add_field(
                    name="Amount",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
                    inline=False
                )
                admin_embed.add_field(
                    name="Ticket ID",
                    value=f"#{ticket_id}",
                    inline=False
                )

                try:
                    await admin.send(embed=admin_embed)
                except discord.Forbidden:
                    continue





    @has_account()
    @commands.command()
    async def withdraw(self, ctx, amount=None, *, rsn=None):
        """Create a withdraw request"""
        if not amount or not rsn:
            await ctx.send("<:remove:1328511957208268800> Please use the correct format\nExample: `,withdraw 100M Zezima`")
            return
        
        formatted_amount = self.parse_amount(amount)
        if not formatted_amount:
            await ctx.send("<:remove:1328511957208268800> Invalid amount format! Please use K, M, B, or T (e.g., 100M, 1B)")
            return

        confirm_embed = discord.Embed(
            title="📝 Confirm Withdraw Request",
            description="Please verify the following details are correct:",
            color=discord.Color.gold()
        )
        confirm_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
            inline=False
        )
        confirm_embed.add_field(
            name="RSN",
            value=rsn,
            inline=False
        )

        view = ConfirmView(timeout=30)
        confirm_msg = await ctx.send(embed=confirm_embed, view=view)
        
        try:
            await ctx.message.delete()
        except:
            pass

        await view.wait()
        
        if view.value is None:
            await confirm_msg.edit(content="<:remove:1328511957208268800> Confirmation timed out. Please try again.", embed=None, view=None)
            return
        
        if view.value is False:
            await confirm_msg.edit(content="<:remove:1328511957208268800> Withdraw request cancelled.", embed=None, view=None)
            return
        
        await confirm_msg.delete()
        
        ticket_id = self.generate_ticket_id()
        ticket_data = {
            "user_id": str(ctx.author.id),
            "user_name": str(ctx.author),
            "amount": formatted_amount,
            "rsn": rsn,
            "date": discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        self.tickets["withdraw"][ticket_id] = ticket_data
        self.save_tickets()

        user_embed = discord.Embed(
            title="<:add:1328511998647861390> Withdraw Request Sent",
            description="Your withdraw request has been sent to an administrator.",
            color=discord.Color.green()
        )
        user_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
            inline=False
        )
        user_embed.add_field(
            name="RSN",
            value=rsn,
            inline=False
        )
        user_embed.add_field(
            name="Ticket ID",
            value=f"#{ticket_id}",
            inline=False
        )
        user_embed.set_footer(text="Please wait for an administrator to process your request.")
        await ctx.send(embed=user_embed)

        for admin_id in self.admin_ids:
            admin = self.bot.get_user(admin_id)
            if admin:
                admin_embed = discord.Embed(
                    title="<:add:1328511998647861390> New Withdraw Request",
                    description=f"A new withdraw request has been submitted.",
                    color=discord.Color.green()
                )
                admin_embed.add_field(
                    name="User",
                    value=ctx.author.mention,
                    inline=False
                )
                admin_embed.add_field(
                    name="Amount",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",
                    inline=False
                )
                admin_embed.add_field(
                    name="Ticket ID",
                    value=f"#{ticket_id}",
                    inline=False
                )

                try:
                    await admin.send(embed=admin_embed)
                except discord.Forbidden:
                    continue



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
                
        if not isinstance(message.channel, discord.DMChannel):
            return

        admin_id = str(message.author.id)
        admin_sessions = []
        
        for user_id, session in self.active_sessions.items():
            if session['admin_id'] == admin_id:
                admin_sessions.append((user_id, session['ticket_id']))

        if admin_sessions:
            if len(admin_sessions) > 1 and not message.content.startswith('#'):
                await message.channel.send("<:remove:1328511957208268800> You have multiple active sessions. Please start your message with the ticket number (e.g., '#1234 Your message')")
                await message.add_reaction("❌")
                return
                
            if len(admin_sessions) > 1:
                try:
                    ticket_num = message.content.split()[0][1:]
                    message_content = ' '.join(message.content.split()[1:])
                    
                    target_user_id = None
                    for user_id, ticket_id in admin_sessions:
                        if ticket_id == ticket_num:
                            target_user_id = user_id
                            break
                    
                    if not target_user_id:
                        await message.channel.send(f"<:remove:1328511957208268800> No active session found with ticket #{ticket_num}")
                        await message.add_reaction("❌")
                        return
                except:
                    await message.channel.send("<:remove:1328511957208268800> Invalid ticket number format. Use '#1234 Your message'")
                    await message.add_reaction("❌")
                    return
            else:
                target_user_id = admin_sessions[0][0]
                message_content = message.content

            user = self.bot.get_user(int(target_user_id))
            if user:
                try:
                    embed = discord.Embed(
                        title="💬 Message from Staff",
                        description=message_content,
                        color=discord.Color.gold()
                    )
                    embed.set_author(
                        name=f"{message.author}",
                        icon_url=message.author.avatar.url if message.author.avatar else None
                    )
                    embed.set_footer(text=f"Ticket #{session['ticket_id']}")
                    
                    await user.send(embed=embed)
                    await message.add_reaction("✅")
                except discord.Forbidden:
                    await message.add_reaction("❌")
            return

        user_id = str(message.author.id)
        if user_id not in self.active_sessions:
            await message.channel.send("<:remove:1328511957208268800> I don't respond to DMs!\nIf theres a green checkmark below to your message, it means I've received it.")
            await message.add_reaction("❌")
            return

        session = self.active_sessions[user_id]
        admin = self.bot.get_user(int(session['admin_id']))
        
        if admin:
            embed = discord.Embed(
                title=f"💬 Message from Client",
                description=message.content,
                color=discord.Color.gold()
            )
            embed.set_author(
                name=f"{message.author}",
                icon_url=message.author.avatar.url if message.author.avatar else None
            )
            embed.set_footer(text=f"Ticket #{session['ticket_id']}")
            
            try:
                await admin.send(embed=embed)
                await message.add_reaction("✅")
            except discord.Forbidden:
                await message.add_reaction("❌")


        if user_id not in self.active_sessions:
            await message.channel.send("<:remove:1328511957208268800> I don't respond to DMs!\nIf theres a green checkmark below to your message, it means I've received it.")
            await message.add_reaction("❌")
            return                

async def setup(bot):
    await asyncio.sleep(0.5)
    
    await bot.add_cog(GambleSystem(bot))

