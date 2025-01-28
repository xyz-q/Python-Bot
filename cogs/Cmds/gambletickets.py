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
        self.user_timer = user_timer  # User's timer message
        self.dm_timer = dm_timer      # Admin's timer message
        self.user_embed = user_embed  # User's embed message
        self.admin_embed = admin_embed # Admin's embed message

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.green)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.bot.get_user(int(self.user_id))
        timer_id = f"{interaction.user.id}_{self.user_id}"
        self.cog.active_timers[timer_id] = False        
        if user:
            await self.user_timer.edit(content="✅ Trade completed! Thank you for using our services!")
            await self.user_embed.delete()

        # Delete public messages
        await self.public_msg.delete()
        await self.timer_msg.delete()
        
        # Update DM messages
        await self.admin_embed.delete()
        await self.dm_timer.edit(content="✅ Trade completed!")
        
        # Remove ticket
        if self.ticket_data['ticket_id'] in self.cog.tickets[self.ticket_type]:
            del self.cog.tickets[self.ticket_type][self.ticket_data['ticket_id']]
            self.cog.save_tickets()
        
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.bot.get_user(int(self.user_id))
        timer_id = f"{interaction.user.id}_{self.user_id}"
        self.cog.active_timers[timer_id] = False
        if user:
            await self.user_timer.edit(content="❌ Trade cancelled by the admin.")
            await self.user_embed.delete()
        
        # Delete public messages
        await self.public_msg.delete()
        await self.timer_msg.delete()
        
        # Update DM messages
        await self.admin_embed.delete()
        await self.dm_timer.edit(content="❌ Trade cancelled!")
        
        # Remove ticket
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
        # Add navigation buttons
        self.first_page = Button(label="⏮", custom_id="first", style=discord.ButtonStyle.grey)
        self.prev_page = Button(label="◀", custom_id="previous", style=discord.ButtonStyle.primary)
        self.next_page = Button(label="▶", custom_id="next", style=discord.ButtonStyle.primary)
        self.last_page = Button(label="⏭", custom_id="last", style=discord.ButtonStyle.grey)
        
        # Add close button
        self.close_button = Button(
            label="✖", 
            custom_id="close", 
            style=discord.ButtonStyle.danger,
            row=1  # Put it on a new row
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
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name=f"{ticket_type.title()} Ticket #{ticket_id}",
            value=f"**User**\n{ticket['user_name']}\n\n"
                f"**Amount**\n<:goldpoints:1319902464115343473> {self.cog.format_amount2(ticket['amount'])}\n\n"  # Changed here
                f"**RSN**\n{ticket['rsn']}\n\n"
                f"**Date**\n{ticket['date']}",
            inline=False
        )
        
        quick_actions = f"✅ `,ticket accept {ticket_id}`\n❌ `,ticket decline {ticket_id}`"
        embed.add_field(name="Quick Actions", value=quick_actions, inline=False)
        
        embed.set_footer(text=f"Ticket ID: #{ticket_id} • Use arrow buttons to navigate")
        return embed

    async def on_timeout(self):
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Try to update the message with disabled buttons
        try:
            if self.message:
                await self.message.delete()
        except:
            pass  

class GambleSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_ids = [110927272210354176, 311612585524854805]  # Replace with actual admin IDs
        self.tickets_file = ".json/tickets.json"
        self.load_tickets()
        self.message = None
        self.active_timers = {}
        self.currency = {}
        self.currency_file = ".json/currency.json"  # Adjust path as needed
        self.load_currency()
        self.MIN_DEPOSIT = 5_000_000  # 1M minimum
        self.MAX_DEPOSIT = 5_000_000_000  # 1T maximum
        self.MIN_WITHDRAW = 10_000_000  # 1M minimum
        self.MAX_WITHDRAW = 250_000_000         


    def is_house_name(self, name: str) -> bool:
        """Check if a name contains 'house' (case-insensitive)"""
        return 'house' in str(name).lower()

    async def validate_user(self, user: typing.Union[discord.Member, str]) -> tuple[str, str, bool]:
        """
        Validates a user input and returns (user_id, display_name, is_valid)
        """
        try:
            # Handle "house" keyword to return bot's ID
            if isinstance(user, str) and user.lower().strip() == "house":
                return str(self.bot.user.id), "🏦 House", True
            
            # Handle discord Member
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
                    print(f"Currency loaded successfully from {self.currency_file}")
            else:
                print(f"Currency file not found at {self.currency_file}")
        except Exception as e:
            print(f"Error loading currency file: {e}")
            self.currency = {}

    async def get_balance(self, user_id) -> int:
        """Get balance for any user or house"""
        try:
            # Convert user_id to string
            str_user_id = str(user_id)
            
            # Handle house account without using upper()
            if str_user_id == "HOUSE" or str_user_id == "house":
                str_user_id = "1233966655923552370"
            
            # Get and return balance
            return int(self.currency.get(str_user_id, 0))
            
        except Exception as e:
            print(f"Error in get_balance for user_id {user_id}: {e}")
            return 0

    def parse_amount(self, amount_str):
        try:
            # First convert to string, then do the operations
            amount_str = str(amount_str).replace(',', '').upper().strip()
            
            multipliers = {
                'K': 1000,
                'M': 1000000,
                'B': 1000000000,
                'T': 1000000000000
            }
            
            # Extract number and multiplier
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
                
            # Convert to float first
            amount = float(number)
            
            # Apply multiplier if exists
            if multiplier in multipliers:
                amount *= multipliers[multiplier]
                
            return int(amount)
            
        except (ValueError, TypeError):
            return None

    def format_amount2(self, amount):
        # For amounts >= 1T
        if amount >= 1000000000000:  # 1T+
            if amount >= 10000000000000:  # 10T+
                trillions = amount / 1000000000000
                return f"{int(trillions):,}T"
            else:
                billions = amount / 1000000000
                return f"{int(billions):,}B"
                
        # For amounts >= 1B
        elif amount >= 1000000000:  # 1B+
            if amount >= 10000000000:  # 10B+
                billions = amount / 1000000000
                return f"{int(billions):,}B"
            else:
                millions = amount / 1000000
                return f"{int(millions):,}M"
                
        # For amounts >= 1M
        elif amount >= 1000000:  # 1M+
            if amount >= 10000000:  # 10M+
                millions = amount / 1000000
                return f"{int(millions):,}M"
            else:
                thousands = amount / 1000
                return f"{int(thousands):,}K"
                
        # For amounts >= 1K
        elif amount >= 1000:
            thousands = amount / 1000
            return f"{int(thousands):,}K"
        
        return f"{int(amount):,}"


    async def update_timer_message(self, message, end_time, user_id, customer_id, dm_message=None, public_msg=None, user_msg=None, admin_msg=None):
        try:
            timer_id = f"{user_id}_{customer_id}"
            self.active_timers[timer_id] = True  # Start timer

            user = self.bot.get_user(int(customer_id))
            
            while self.active_timers.get(timer_id, False):  # Check if timer should continue
                now = datetime.datetime.now()
                time_left = end_time - now
                
                if time_left.total_seconds() <= 0:
                    # Timer expired logic...
                    break
                    
                minutes = int(time_left.total_seconds() // 60)
                seconds = int(time_left.total_seconds() % 60)
                
                timer_text = f"⏳ Time remaining: {minutes}m {seconds}s"
                
                # Update user's timer message
                if user_msg:
                    try:
                        await user_msg.edit(content=timer_text)
                    except:
                        pass
                
                # Update admin's timer message
                if dm_message:
                    try:
                        await dm_message.edit(content=timer_text)
                    except:
                        pass
                
                await asyncio.sleep(17)

            # Clean up timer reference
            if timer_id in self.active_timers:
                del self.active_timers[timer_id]

        except Exception as e:
            print(f"Error in update_timer_message: {e}")



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

    def save_tickets(self):
        data = {
            "tickets": self.tickets,
            "last_ticket_id": self.last_ticket_id
        }
        with open(self.tickets_file, 'w') as f:
            json.dump(data, f, indent=4)



    @commands.group(invoke_without_command=True, aliases=["tickets"])
    async def ticket(self, ctx):
        """Ticket management system"""
        embed = discord.Embed(
            title="🎫 Ticket System Commands",
            description="Here are all available ticket commands:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="User Commands",
            value="`,ticket list` - View your tickets\n"
                  "`,ticket cancel <ticket_id>` - Cancel your ticket",
            inline=False
        )
        
        if str(ctx.author.id) in map(str, self.admin_ids):
            embed.add_field(
                name="Admin Commands",
                value="`,ticket admin [deposit/withdraw]` - View all pending tickets\n"
                      "`,ticket accept <ticket_id>` - Accept a ticket\n"
                      "`,ticket decline <ticket_id>` - Decline a ticket",
                inline=False
            )
        
        embed.set_footer(text="Use ,deposit <amount> <rsn> or ,withdraw <amount> <rsn> to create new tickets")
        await ctx.send(embed=embed)

    @ticket.command(name="list")
    async def ticket_list(self, ctx, type=None):
        await ctx.message.delete()
        """List your pending tickets"""
        if type and type not in ["deposit", "withdraw"]:
            await ctx.send("❌ Invalid type! Use 'deposit' or 'withdraw'")
            return

        # Collect user's tickets into a list
        tickets_list = []
        types_to_show = [type] if type else ["deposit", "withdraw"]
        
        for t in types_to_show:
            for ticket_id, ticket in self.tickets[t].items():
                # Only add tickets that belong to this user
                if str(ticket['user_id']) == str(ctx.author.id):
                    tickets_list.append((t, ticket_id, ticket))

        if not tickets_list:
            await ctx.send("❌ You have no pending tickets!")
            return

        # Create pagination view with cog instance
        view = TicketPaginationView(tickets_list, self)  # Pass self (cog) instead of bot
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)

    @ticket.command(name="admin")
    async def admin_list(self, ctx, type=None):
        await ctx.message.delete()
        """List all pending tickets (Admin only)"""
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("❌ You don't have permission to use this command!")
            return

        if type and type not in ["deposit", "withdraw"]:
            await ctx.send("❌ Invalid type! Use 'deposit' or 'withdraw'")
            return

        tickets_list = []
        types_to_show = [type] if type else ["deposit", "withdraw"]
        
        for t in types_to_show:
            for ticket_id, ticket in self.tickets[t].items():
                tickets_list.append((t, ticket_id, ticket))

        if not tickets_list:
            await ctx.send("❌ No pending tickets found!")
            return

        view = TicketPaginationView(tickets_list, self)  # Changed from bot=self.bot to just self
        embed = view.create_embed()
        view.message = await ctx.send(embed=embed, view=view)


    @ticket.command(name="accept")
    async def accept_ticket(self, ctx, ticket_id: str):
        """Accept a ticket (Admin only)"""
        await ctx.message.delete()
        
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("❌ You don't have permission to use this command!")
            return

        ticket_type = None
        ticket_data = None
        for type in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[type]:
                ticket_type = type
                ticket_data = self.tickets[type][ticket_id]
                break

        if not ticket_data:
            await ctx.send("❌ Invalid ticket ID!")
            return

        user = self.bot.get_user(int(ticket_data['user_id']))
        ticket_data['ticket_id'] = ticket_id  # Add ticket_id to the data

        # Get admin details for both deposit and withdraw
        question_msg = await ctx.send("Please enter your RSN:")
        
        try:
            rsn_response = await self.bot.wait_for(
                'message',
                timeout=30.0,
                check=lambda message: message.author == ctx.author and message.channel == ctx.channel
            )
            print(rsn_response.content)  # This shows correct case
            await rsn_response.delete()
            admin_rsn = str(rsn_response.content)  # Store the exact original content

            
            await question_msg.edit(content="Please enter your combat level:")
            level_response = await self.bot.wait_for(
                'message',
                timeout=30.0,
                check=lambda message: message.author == ctx.author and message.channel == ctx.channel
            )
            await level_response.delete()
            admin_level = level_response.content
            
            await question_msg.edit(content="Please enter the world number:")
            world_response = await self.bot.wait_for(
                'message',
                timeout=30.0,
                check=lambda message: message.author == ctx.author and message.channel == ctx.channel
            )
            await world_response.delete()
            world = world_response.content


            await question_msg.edit(content="Please enter the location:")
            location_response = await self.bot.wait_for(
                'message',
                timeout=30.0,
                check=lambda message: message.author == ctx.author and message.channel == ctx.channel
            )
            await location_response.delete()
            location = location_response.content.title()  # This will capitalize first letter of each word

            await question_msg.delete()
            
            # Create embed for user and channel
            user_embed = discord.Embed(
                title="✅ Active Trade Session\n       ",
                description=f"Your {ticket_type} request has been approved.",
                color=discord.Color.green()
            )
            user_embed.add_field(
                name="Admin Details",
                value=f"RSN: {admin_rsn}\nCombat Level: {admin_level}",
                inline=False
            )
            user_embed.add_field(
                name="Meeting Point",
                value=f"World {world}\nLocation: {location}",  # Modified to include location
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
            
            # Create embed for admin DM
            admin_embed = user_embed.copy()
            admin_embed.title = f"🎫 Active {ticket_type} "
            admin_embed.description = f"Ticket ID: {ticket_id} for {ticket_data['user_name']}"
            
            # Send to user with initial timer
            if user:
                user_embed_msg = await user.send(embed=user_embed)
                user_timer_msg = await user.send("⏳ Time remaining: 10m 0s")
            
            # Send to channel for reference
            public_msg = await ctx.send("✅ Trade session started.")
            timer_msg = await ctx.send(f"Ticket #{ticket_id} accepted by {ctx.author}.")
            
            # Send DM to admin with controls
            admin_embed_msg = await ctx.author.send(embed=admin_embed)
            admin_timer_msg = await ctx.author.send("⏳ Time remaining: 10m 0s")
            
            # Add buttons to admin DM
            admin_view = AdminTicketView(
                self.bot, 
                ticket_data['user_id'], 
                timer_msg, 
                ticket_data, 
                public_msg, 
                self, 
                ticket_type,
                user_timer_msg,     # User's timer message
                admin_timer_msg,    # Admin's timer message
                user_embed_msg,     # User's embed message
                admin_embed_msg     # Admin's embed message
            )
            await admin_embed_msg.edit(view=admin_view)
            
            # Start timer
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
            await self.update_timer_message(
                timer_msg, 
                end_time, 
                ctx.author.id, 
                ticket_data['user_id'], 
                admin_timer_msg, 
                public_msg,
                user_timer_msg,
                admin_embed_msg
            )

        except asyncio.TimeoutError:
            await question_msg.delete()
            await ctx.send("❌ Timed out waiting for response.", delete_after=5)
            return





    @ticket.command(name="decline")
    async def decline_ticket(self, ctx, ticket_id: str):
        """Decline a ticket (Admin only)"""
        if str(ctx.author.id) not in map(str, self.admin_ids):
            await ctx.send("❌ You don't have permission to use this command!")
            return

        ticket_type = None
        ticket_data = None
        for type in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[type]:
                ticket_type = type
                ticket_data = self.tickets[type][ticket_id]
                break

        if not ticket_data:
            await ctx.send("❌ Invalid ticket ID!")
            return

        user = self.bot.get_user(int(ticket_data['user_id']))
        
        # Notify user
        if user:
            embed = discord.Embed(
                title="❌ Request Declined",
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
            embed.set_footer(text=f"Declined by {ctx.author}")
            await user.send(embed=embed)

        # Remove ticket
        del self.tickets[ticket_type][ticket_id]
        self.save_tickets()
        await ctx.send(f"❌ Ticket #{ticket_id} has been declined!")

    @ticket.command(name="cancel")
    async def cancel_ticket(self, ctx, ticket_id: str):
        """Cancel your own ticket"""
        ticket_type = None
        ticket_data = None
        for type in ["deposit", "withdraw"]:
            if ticket_id in self.tickets[type]:
                ticket_type = type
                ticket_data = self.tickets[type][ticket_id]
                break

        if not ticket_data:
            await ctx.send("❌ Invalid ticket ID!")
            return

        if str(ticket_data['user_id']) != str(ctx.author.id):
            await ctx.send("❌ You can only cancel your own tickets!")
            return

        # Remove ticket
        del self.tickets[ticket_type][ticket_id]
        self.save_tickets()
        await ctx.send(f"✅ Your ticket #{ticket_id} has been cancelled!")

    def generate_ticket_id(self):
        self.last_ticket_id += 1
        return str(self.last_ticket_id)    

    @commands.command()
    async def deposit(self, ctx, amount=None, *, rsn=None):
        """Create a deposit request"""
        if not amount or not rsn:
            await ctx.send("❌ Please use the correct format: `,deposit <amount> <rsn>`\nExample: `,deposit 100M Zezima`")
            return

        formatted_amount = self.parse_amount(amount)
        if formatted_amount < self.MIN_DEPOSIT:
            await ctx.send(f"❌ Minimum deposit amount is {self.format_amount2(self.MIN_DEPOSIT)} <:goldpoints:1319902464115343473>")
            return
            
        if formatted_amount > self.MAX_DEPOSIT:
            await ctx.send(f"❌ Maximum deposit amount is {self.format_amount2(self.MAX_DEPOSIT)} <:goldpoints:1319902464115343473>")
            return
        if not formatted_amount:
            await ctx.send("❌ Invalid amount format! Please use K, M, B, or T (e.g., 100M, 1B)")
            return

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

        # User notification embed
        user_embed = discord.Embed(
            title="💰 Deposit Request Sent",
            description="Your deposit request has been sent to an administrator.",
            color=discord.Color.green()
        )
        # User notification embed
        user_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",  # Changed here
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

        # Admin notification embed
        for admin_id in self.admin_ids:
            admin = self.bot.get_user(admin_id)
            if admin:
                admin_embed = discord.Embed(
                    title="💰 New Deposit Request",
                    description=f"A new deposit request has been submitted.",
                    color=discord.Color.green()
                )
                admin_embed.add_field(
                    name="User",
                    value=ctx.author.mention,
                    inline=False
                )
                admin_embed.add_field(
                    name="Amount",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",  # Changed here
                    inline=False
                )
                admin_embed.add_field(
                    name="RSN",
                    value=rsn,
                    inline=False
                )
                admin_embed.add_field(
                    name="Ticket ID",
                    value=f"#{ticket_id}",
                    inline=False
                )
                admin_embed.set_footer(text="Use ,ticket accept/decline to process this request")
                try:
                    await admin.send(embed=admin_embed)
                except discord.Forbidden:
                    continue

    @commands.command()                  
    async def withdraw(self, ctx, amount=None, *, rsn=None):
        """Create a withdrawal request"""
        if not amount or not rsn:
            await ctx.send("❌ Please use the correct format: `,withdraw <amount> <rsn>`\nExample: `,withdraw 100M Zezima`")
            return

        formatted_amount = self.parse_amount(amount)
        if not formatted_amount:
            await ctx.send("❌ Invalid amount format! Please use K, M, B, or T (e.g., 100M, 1B)")
            return

        # Simple limit checks
        if formatted_amount < self.MIN_WITHDRAW:
            await ctx.send(f"❌ Minimum withdrawal amount is {self.format_amount2(self.MIN_WITHDRAW)} <:goldpoints:1319902464115343473>")
            return
            
        if formatted_amount > self.MAX_WITHDRAW:
            await ctx.send(f"❌ Maximum withdrawal amount is {self.format_amount2(self.MAX_WITHDRAW)} <:goldpoints:1319902464115343473>")
            return
        



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

        # User notification embed
        user_embed = discord.Embed(
            title="💸 Withdrawal Request Sent",
            description="Your withdrawal request has been sent to an administrator.",
            color=discord.Color.green()
        )
        # User notification embed
        user_embed.add_field(
            name="Amount",
            value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",  # Changed here
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

        # Admin notification embed
        for admin_id in self.admin_ids:
            admin = self.bot.get_user(admin_id)
            if admin:
                admin_embed = discord.Embed(
                    title="💸 New Withdrawal Request",
                    description=f"A new withdrawal request has been submitted.",
                    color=discord.Color.green()
                )
                admin_embed.add_field(
                    name="User",
                    value=ctx.author.mention,
                    inline=False
                )
                # Admin notification embed
                admin_embed.add_field(
                    name="Amount",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount2(formatted_amount)}",  # Changed here
                    inline=False
                )
                admin_embed.add_field(
                    name="Ticket ID",
                    value=f"#{ticket_id}",
                    inline=False
                )
                admin_embed.set_footer(text="Use ,ticket accept/decline to process this request")
                try:
                    await admin.send(embed=admin_embed)
                except discord.Forbidden:
                    continue


async def setup(bot):
    await bot.add_cog(GambleSystem(bot))

