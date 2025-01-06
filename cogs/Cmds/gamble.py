import discord
from discord.ext import commands
from discord.ui import View, Button
import json
from typing import List
import math
import random
import asyncio
import typing



from typing import List
import math
from discord.ui import View, Button

class PaginationView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=30)
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()




class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency = {}
        self.load_currency()
        self.balances = {}
        self.admin_id = 110927272210354176

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
        try:
            with open('currency.json', 'r') as f:
                self.currency = json.load(f)
        except FileNotFoundError:
            self.currency = {}

    def save_currency(self):
        with open('currency.json', 'w') as f:
            json.dump(self.currency, f, indent=4)

    def get_balance(self, user_id):
        return self.currency.get(str(user_id), 0)

    def add_balance(self, user_id, amount):
            user_id = str(user_id)
            if user_id not in self.balances:
                self.balances[user_id] = 0
            self.balances[user_id] += amount
            self.save_data()
            return self.balances[user_id]

    def add_balance(self, user_id, amount):
        user_id = str(user_id)
        if user_id not in self.balances:
            self.balances[user_id] = 0
        self.balances[user_id] += amount
        self.save_data()
        return self.balances[user_id]

    def remove_balance(self, user_id, amount):
        user_id = str(user_id)
        if user_id not in self.balances:
            self.balances[user_id] = 0
        self.balances[user_id] -= amount
        if self.balances[user_id] < 0:
            self.balances[user_id] = 0
        self.save_data()
        return self.balances[user_id]

    def parse_amount(self, amount_str):
        amount_str = amount_str.upper()
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
        
        if any(suffix in amount_str for suffix in multipliers.keys()):
            suffix = amount_str[-1]
            if suffix in multipliers:
                number = float(amount_str[:-1])
                return int(number * multipliers[suffix])
        return int(float(amount_str))

    def format_amount(self, amount):
        if amount >= 1000000000000:  # Trillion
            return f"{amount / 1000000000000:.1f}T"
        elif amount >= 1000000000:  # Billion
            return f"{amount / 1000000000:.1f}B"
        elif amount >= 1000000:  # Million
            return f"{amount / 1000000:.1f}M"
        elif amount >= 1000:  # Thousand
            return f"{amount / 1000:.1f}K"
        return str(amount)

    class ConfirmView(View):
        def __init__(self, timeout=15):
            super().__init__(timeout=timeout)
            self.value = None

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: Button):
            self.value = True
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: Button):
            self.value = False
            self.stop()
            await interaction.response.defer()

    async def get_balance(self, user_id: str) -> int:
        """Get balance for any user or house"""
        # Convert user_id to string if it isn't already
        user_id = str(user_id)
        
        # Handle "HOUSE" case (case-insensitive)
        if isinstance(user_id, str) and user_id.upper() == "HOUSE":
            user_id = "1233966655923552370"
        
        return self.currency.get(user_id, 0)

  



    @commands.command(aliases=['balances', 'bals'])
    async def balancelist(self, ctx):
        if not self.currency:
            await ctx.send("No balances found!")
            return

        # Filter out the house account and convert user IDs to int for sorting
        user_balances = []
        house_balance = 0
        
        for user_id, balance in self.currency.items():
            if user_id == "1233966655923552370":
                house_balance = balance
            else:
                try:
                    user_balances.append((int(user_id), balance))
                except ValueError:
                    continue

        # Sort by balance (highest to lowest)
        sorted_balances = sorted(user_balances, key=lambda x: x[1], reverse=True)

        # Create pages of 10 entries each
        entries_per_page = 10
        pages = []
        current_page = []
        
        # Add house balance at the top of the first page if it exists
        if house_balance > 0:
            current_page.append(f"🏦 House: <:goldpoints:1319902464115343473> {self.format_amount(house_balance)}")

        for index, (user_id, balance) in enumerate(sorted_balances, 1):
            try:
                user = await self.bot.fetch_user(user_id)
                username = user.name
            except:
                username = f"Unknown User ({user_id})"

            entry = f"{index}. {username}: <:goldpoints:1319902464115343473> {self.format_amount(balance)}"
            current_page.append(entry)

            if len(current_page) == entries_per_page:
                pages.append("\n".join(current_page))
                current_page = []

        if current_page:
            pages.append("\n".join(current_page))

        if not pages:
            await ctx.send("No balances found!")
            return

        # Create embeds for each page
        embeds = []
        for i, page in enumerate(pages, 1):
            embed = discord.Embed(
                title="💰 Balance Rankings",
                description=page,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Page {i}/{len(pages)}")
            embeds.append(embed)

        # Send the first embed with pagination
        view = PaginationView(embeds)
        message = await ctx.send(embed=embeds[0], view=view)
        view.message = message  # Store message reference for timeout handling

    

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, *, user: typing.Optional[typing.Union[discord.Member, str]] = None):
        """Check your balance or someone else's balance"""
        try:
            if user is None:
                # Check own balance
                if self.is_house_name(ctx.author.name):
                    await ctx.send("Error: Cannot check balance for users with 'house' in their name.")
                    return
                user_id = str(ctx.author.id)
                user_name = ctx.author.name
            else:
                user_id, user_name, valid = await self.validate_user(user)
                if not valid:
                    await ctx.send("Error: Invalid user! Please mention a valid user or type 'house'. Users with 'house' in their name are not allowed.")
                    return

            balance = await self.get_balance(user_id)
            
            embed = discord.Embed(
                title=f"{user_name}'s Balance",
                description=f"<:goldpoints:1319902464115343473> {self.format_amount(balance)}",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, args=None):
        """Add currency to a user's balance (Admin only)"""
        try:
            if not args:
                await ctx.send("Please provide a user and amount! Example: ,add @user 1000 or ,add house 1000")
                return

            # Split args into user and amount
            args_split = args.rsplit(' ', 1)
            if len(args_split) != 2:
                await ctx.send("Invalid format! Example: ,add @user 1000 or ,add house 1000")
                return

            user_arg, amount = args_split

            # Convert user mention to Member or keep as string for "house"
            if user_arg.lower() == "house":
                user = "house"
            else:
                # Try to get member from mention or name
                try:
                    user = await commands.MemberConverter().convert(ctx, user_arg)
                except:
                    await ctx.send("Invalid user! Please mention a valid user or type 'house'.")
                    return

            # Validate user
            user_id, user_name, valid = await self.validate_user(user)
            if not valid:
                await ctx.send("Error: Invalid user! Please mention a valid user or type 'house'.")
                return

            # Parse amount
            try:
                amount = self.parse_amount(amount)
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return

            # Create confirmation view
            view = self.ConfirmView()
            confirm_msg = await ctx.send(
                f"Are you sure you want to add <:goldpoints:1319902464115343473> {self.format_amount(amount)} to {user_name}'s balance?",
                view=view
            )

            await view.wait()
            
            if view.value:
                # Add balance
                if user_id not in self.currency:
                    self.currency[user_id] = 0
                self.currency[user_id] += amount
                
                # Save changes
                self.save_currency()
                
                # Create success embed
                embed = discord.Embed(
                    title="Addition Successful!",
                    description=f"Added <:goldpoints:1319902464115343473> {self.format_amount(amount)} to {user_name}'s balance",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="New Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(await self.get_balance(user_id))}"
                )
                
                await confirm_msg.edit(content=None, embed=embed, view=None)
            else:
                await confirm_msg.edit(content="Addition cancelled.", view=None)
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, args=None):
        """Remove currency from a user's balance (Admin only)"""
        try:
            if not args:
                await ctx.send("Please provide a user and amount! Example: ,remove @user 1000 or ,remove house 1000")
                return

            # Split args into user and amount
            args_split = args.rsplit(' ', 1)
            if len(args_split) != 2:
                await ctx.send("Invalid format! Example: ,remove @user 1000 or ,remove house 1000")
                return

            user_arg, amount = args_split

            # Convert user mention to Member or keep as string for "house"
            if user_arg.lower() == "house":
                user = "house"
            else:
                # Try to get member from mention or name
                try:
                    user = await commands.MemberConverter().convert(ctx, user_arg)
                except:
                    await ctx.send("Invalid user! Please mention a valid user or type 'house'.")
                    return

            # Validate user
            user_id, user_name, valid = await self.validate_user(user)
            if not valid:
                await ctx.send("Error: Invalid user! Please mention a valid user or type 'house'.")
                return

            # Parse amount
            try:
                amount = self.parse_amount(amount)
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return

            # Check if user has enough balance
            current_balance = await self.get_balance(user_id)
            if current_balance < amount:
                await ctx.send(f"{user_name} doesn't have enough balance!")
                return

            # Create confirmation view
            view = self.ConfirmView()
            confirm_msg = await ctx.send(
                f"Are you sure you want to remove <:goldpoints:1319902464115343473> {self.format_amount(amount)} from {user_name}'s balance?",
                view=view
            )

            await view.wait()
            
            if view.value:
                # Remove balance
                self.currency[user_id] -= amount
                
                # Save changes
                self.save_currency()
                
                # Create success embed
                embed = discord.Embed(
                    title="Removal Successful!",
                    description=f"Removed <:goldpoints:1319902464115343473> {self.format_amount(amount)} from {user_name}'s balance",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="New Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(await self.get_balance(user_id))}"
                )
                
                await confirm_msg.edit(content=None, embed=embed, view=None)
            else:
                await confirm_msg.edit(content="Removal cancelled.", view=None)
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command()
    async def transfer(self, ctx, *, args=None):
        """Transfer currency to another user"""
        try:
            if not args:
                await ctx.send("Please provide a recipient and amount! Example: ,transfer @user 1000 or ,transfer house 1000")
                return

            # Split args into recipient and amount
            args_split = args.rsplit(' ', 1)
            if len(args_split) != 2:
                await ctx.send("Invalid format! Example: ,transfer @user 1000 or ,transfer house 1000")
                return

            recipient_arg, amount = args_split

            # Convert recipient mention to Member or keep as string for "house"
            if recipient_arg.lower() == "house":
                recipient = "house"
            else:
                # Try to get member from mention or name
                try:
                    recipient = await commands.MemberConverter().convert(ctx, recipient_arg)
                except:
                    await ctx.send("Invalid recipient! Please mention a valid user or type 'house'.")
                    return

            # Validate recipient
            recipient_id, recipient_name, valid = await self.validate_user(recipient)
            if not valid:
                await ctx.send("Error: Invalid recipient! Please mention a valid user or type 'house'.")
                return

            # Parse amount
            try:
                amount = self.parse_amount(amount)
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            sender_id = str(ctx.author.id)
            
            # Check if sender has enough balance
            sender_balance = await self.get_balance(sender_id)
            
            if sender_id == recipient_id:
                await ctx.send("You cannot transfer to yourself!")
                return

            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return

            if sender_balance < amount:
                await ctx.send(f"You don't have enough balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(sender_balance)}")
                return

            # Create confirmation view
            view = self.ConfirmView()
            confirm_msg = await ctx.send(
                f"Are you sure you want to transfer <:goldpoints:1319902464115343473> {self.format_amount(amount)} to {recipient_name}?",
                view=view
            )

            await view.wait()
            
            if view.value:
                # Remove from sender
                self.currency[sender_id] -= amount
                
                # Add to recipient
                if recipient_id not in self.currency:
                    self.currency[recipient_id] = 0
                self.currency[recipient_id] += amount
                
                # Save changes
                self.save_currency()
                
                # Get new balance
                new_balance = await self.get_balance(sender_id)
                
                embed = discord.Embed(
                    title="Transfer Successful!",
                    description=f"Transferred <:goldpoints:1319902464115343473> {self.format_amount(amount)} to {recipient_name}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Your New Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(new_balance)}"
                )
                
                await confirm_msg.edit(content=None, embed=embed, view=None)
            else:
                await confirm_msg.edit(content="Transfer cancelled.", view=None)
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")



    @commands.command()
    async def staking(self, ctx):
        """Shows all available economy commands"""
        # Delete the invoked command message
        await ctx.message.delete()

        # Get all commands from this cog
        commands_list = sorted(
            [cmd for cmd in self.bot.get_cog('Economy').get_commands()],
            key=lambda x: x.name
        )

        # Create command descriptions
        command_descriptions = []
        for cmd in commands_list:
            aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            description = cmd.help or "No description available"
            command_descriptions.append(f"`,{cmd.name}{aliases}`")

        # Split into pages (5 commands per page)
        pages = []
        page_size = 5
        for i in range(0, len(command_descriptions), page_size):
            page = "\n".join(command_descriptions[i:i + page_size])
            pages.append(page)

        # Create embeds for each page
        embeds = []
        for i, page in enumerate(pages, 1):
            embed = discord.Embed(
                title="Economy Commands",
                description=page,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Page {i}/{len(pages)} • Command list will be deleted after 30s of inactivity")
            embeds.append(embed)

        # Send message with pagination
        view = PaginationView(embeds)
        await ctx.send(embed=embeds[0], view=view)


    @commands.command()
    async def deposit(self, ctx, amount: str = None, *, rsn: str = None):
        """Request a deposit with amount and RSN"""
        try:
            if amount is None or rsn is None:
                await ctx.send("❌ Please provide both amount and RSN!\nUsage: `,deposit <amount> <rsn>`\nExample: `,deposit 100M Zezima`")
                return

            # Try to parse the amount to validate it
            try:
                # Assuming you have the parse_amount function
                parsed_amount = self.parse_amount(amount)
                formatted_amount = self.format_amount(parsed_amount)
            except ValueError:
                await ctx.send("❌ Invalid amount! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            # Get admin user
            admin = self.bot.get_user(self.admin_id)
            if not admin:
                await ctx.send("❌ Unable to process request at this time. Please contact an administrator.")
                return

            # Create embed for admin
            admin_embed = discord.Embed(
                title="💰 New Deposit Request",
                color=discord.Color.green()
            )
            admin_embed.add_field(
                name="User",
                value=f"{ctx.author} (ID: {ctx.author.id})",
                inline=False
            )
            admin_embed.add_field(
                name="Amount",
                value=f"<:goldpoints:1319902464115343473> {formatted_amount}",
                inline=False
            )
            admin_embed.add_field(
                name="RSN",
                value=rsn,
                inline=False
            )
            admin_embed.set_footer(text=f"Requested at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Send DM to admin
            try:
                await admin.send(embed=admin_embed)
            except discord.Forbidden:
                await ctx.send("❌ Unable to process request at this time. Please contact an administrator.")
                return

            # Confirmation embed for user
            user_embed = discord.Embed(
                title="💰 Deposit Request Sent",
                description="Your deposit request has been sent to an administrator.",
                color=discord.Color.green()
            )
            user_embed.add_field(
                name="Amount",
                value=f"<:goldpoints:1319902464115343473> {formatted_amount}",
                inline=False
            )
            user_embed.add_field(
                name="RSN",
                value=rsn,
                inline=False
            )
            user_embed.set_footer(text="Please wait for an administrator to process your request.")

            await ctx.send(embed=user_embed)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @commands.command()
    async def withdraw(self, ctx, amount: str = None, *, rsn: str = None):
        """Request a withdrawal with amount and RSN"""
        try:
            if amount is None or rsn is None:
                await ctx.send("❌ Please provide both amount and RSN!\nUsage: `,withdraw <amount> <rsn>`\nExample: `,withdraw 100M Zezima`")
                return

            # Try to parse the amount to validate it
            try:
                # Assuming you have the parse_amount function
                parsed_amount = self.parse_amount(amount)
                formatted_amount = self.format_amount(parsed_amount)
            except ValueError:
                await ctx.send("❌ Invalid amount! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            # Check if user has enough balance
            user_balance = await self.get_balance(str(ctx.author.id))
            if user_balance < parsed_amount:
                await ctx.send(f"❌ Insufficient balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(user_balance)}")
                return

            # Get admin user
            admin = self.bot.get_user(self.admin_id)
            if not admin:
                await ctx.send("❌ Unable to process request at this time. Please contact an administrator.")
                return

            # Create embed for admin
            admin_embed = discord.Embed(
                title="💸 New Withdrawal Request",
                color=discord.Color.blue()
            )
            admin_embed.add_field(
                name="User",
                value=f"{ctx.author} (ID: {ctx.author.id})",
                inline=False
            )
            admin_embed.add_field(
                name="Amount",
                value=f"<:goldpoints:1319902464115343473> {formatted_amount}",
                inline=False
            )
            admin_embed.add_field(
                name="RSN",
                value=rsn,
                inline=False
            )
            admin_embed.add_field(
                name="User's Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(user_balance)}",
                inline=False
            )
            admin_embed.set_footer(text=f"Requested at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Send DM to admin
            try:
                await admin.send(embed=admin_embed)
            except discord.Forbidden:
                await ctx.send("❌ Unable to process request at this time. Please contact an administrator.")
                return

            # Confirmation embed for user
            user_embed = discord.Embed(
                title="💸 Withdrawal Request Sent",
                description="Your withdrawal request has been sent to an administrator.",
                color=discord.Color.blue()
            )
            user_embed.add_field(
                name="Amount",
                value=f"<:goldpoints:1319902464115343473> {formatted_amount}",
                inline=False
            )
            user_embed.add_field(
                name="RSN",
                value=rsn,
                inline=False
            )
            user_embed.set_footer(text="Please wait for an administrator to process your request.")

            await ctx.send(embed=user_embed)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
    

    @commands.command()
    async def flip(self, ctx, choice: str = None, bet: str = None):
        """Flip a coin and bet on the outcome"""
        try:
            if choice is None or bet is None:
                await ctx.send("Please specify your choice (heads/tails) and bet amount! Example: ,flip heads 1000")
                return

            # Validate choice
            choice = choice.lower()
            if choice not in ['heads', 'tails', 'h', 't']:
                await ctx.send("Invalid choice! Please choose 'heads' or 'tails'")
                return

            # Convert short forms to full
            if choice == 'h':
                choice = 'heads'
            elif choice == 't':
                choice = 'tails'

            # Parse bet amount
            try:
                bet_amount = self.parse_amount(bet)
            except ValueError:
                await ctx.send("Invalid bet amount! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            if bet_amount <= 0:
                await ctx.send("Bet amount must be positive!")
                return

            # Calculate tax amount (5% of bet)
            tax_amount = int(bet_amount * 0.05)  # 5% tax
            win_amount = bet_amount - tax_amount  # Winning amount after tax

            # Check user's balance
            user_id = str(ctx.author.id)
            user_balance = await self.get_balance(user_id)

            if user_balance < bet_amount:
                await ctx.send(f"You don't have enough balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(user_balance)}")
                return

            # Create confirmation embed
            confirm_embed = discord.Embed(
                title="🎲 Confirm Coin Flip",
                color=discord.Color.gold()
            )
            
            confirm_embed.add_field(
                name="Your Bet",
                value=f"**Choice:** {choice.upper()}\n**Amount:** <:goldpoints:1319902464115343473> {self.format_amount(bet_amount)}",
                inline=False
            )
            
            confirm_embed.add_field(
                name="Potential Outcome",
                value=f"**Win:** +<:goldpoints:1319902464115343473> {self.format_amount(win_amount)} (5% house tax: {self.format_amount(tax_amount)})\n"
                    f"**Lose:** -<:goldpoints:1319902464115343473> {self.format_amount(bet_amount)}",
                inline=False
            )
            
            confirm_embed.add_field(
                name="Your Balance",
                value=f"Current: <:goldpoints:1319902464115343473> {self.format_amount(user_balance)}\n"
                    f"If Win: <:goldpoints:1319902464115343473> {self.format_amount(user_balance + win_amount)}\n"
                    f"If Lose: <:goldpoints:1319902464115343473> {self.format_amount(user_balance - bet_amount)}",
                inline=False
            )

            # Create confirmation view
            view = self.ConfirmView()
            confirm_msg = await ctx.send(embed=confirm_embed, view=view)

            await view.wait()
            
            if view.value:
                # Use secrets for better randomization
                import secrets
                result = 'heads' if secrets.randbelow(2) == 0 else 'tails'
                
                # Determine if user won
                won = choice == result
                
                # Calculate winnings/losses and update balances
                if won:
                    # User wins bet amount minus tax
                    self.currency[user_id] += win_amount
                    
                    # House gets the tax
                    house_id = str(self.bot.user.id)
                    if house_id not in self.currency:
                        self.currency[house_id] = 0
                    self.currency[house_id] += tax_amount
                else:
                    # User loses full bet amount
                    self.currency[user_id] -= bet_amount
                    
                    # House gets the full loss
                    house_id = str(self.bot.user.id)
                    if house_id not in self.currency:
                        self.currency[house_id] = 0
                    self.currency[house_id] += bet_amount

                # Save changes
                self.save_currency()
                
                # Get new balance
                new_balance = await self.get_balance(user_id)
                
                # Create result embed
                result_embed = discord.Embed(
                    title="🎲 Coin Flip Result",
                    color=discord.Color.green() if won else discord.Color.red()
                )
                
                result_embed.add_field(
                    name="The Coin Landed On",
                    value=f"**{result.upper()}**",
                    inline=False
                )
                
                result_embed.add_field(
                    name="Your Choice",
                    value=f"**{choice.upper()}**",
                    inline=False
                )
                
                if won:
                    result_embed.add_field(
                        name="You Won!",
                        value=f"+<:goldpoints:1319902464115343473> {self.format_amount(win_amount)}\n"
                            f"House Tax: <:goldpoints:1319902464115343473> {self.format_amount(tax_amount)} (5%)",
                        inline=False
                    )
                else:
                    result_embed.add_field(
                        name="You Lost!",
                        value=f"-<:goldpoints:1319902464115343473> {self.format_amount(bet_amount)}",
                        inline=False
                    )
                    
                result_embed.add_field(
                    name="New Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(new_balance)}",
                    inline=False
                )
                
                await confirm_msg.edit(content=None, embed=result_embed, view=None)
            else:
                cancel_embed = discord.Embed(
                    title="Coin Flip Cancelled",
                    description="The bet has been cancelled.",
                    color=discord.Color.grey()
                )
                await confirm_msg.edit(content=None, embed=cancel_embed, view=None)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command(name="gamble", aliases=["slot", "slots"])
    async def gamble(self, ctx, amount: str):
        try:
            # Parse bet amount
            bet = self.parse_amount(amount)
            user_id = str(ctx.author.id)
            user_balance = await self.get_balance(user_id)
            
            if bet <= 0:
                await ctx.send("You must bet at least 1 coin!")
                return
                
            if bet > user_balance:
                await ctx.send(f"You don't have enough coins! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(user_balance)}")
                return

            # Slot machine symbols with weights and multipliers
            symbols = {
                "💎": {"weight": 1, "multiplier": 50, "name": "Diamond"},    
                "🎰": {"weight": 2, "multiplier": 25, "name": "Jackpot"},    
                "7️⃣": {"weight": 3, "multiplier": 10, "name": "Seven"},    
                "🍀": {"weight": 4, "multiplier": 5, "name": "Clover"},     
                "⭐": {"weight": 5, "multiplier": 3, "name": "Star"},     
                "🎲": {"weight": 6, "multiplier": 2, "name": "Dice"}
            }

            # Create weighted symbol list
            weighted_symbols = []
            for symbol, data in symbols.items():
                weighted_symbols.extend([symbol] * data["weight"])
            
            # Create initial embed
            embed = discord.Embed(
                title="🎰 SLOT MACHINE 🎰", 
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Spinning...", 
                value="| ❓ | ❓ | ❓ |"
            )
            embed.set_footer(
                text=f"Bet: {self.format_amount(bet)} GP"
            )
            
            msg = await ctx.send(embed=embed)
            
            # Generate final results
            final_symbols = [random.choice(weighted_symbols) for _ in range(3)]
            
            # Optimized animation sequence
            await asyncio.sleep(0.5)
            embed.set_field_at(0, name="Spinning...", value=f"| {final_symbols[0]} | ❓ | ❓ |")
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)
            embed.set_field_at(0, name="Spinning...", value=f"| {final_symbols[0]} | {final_symbols[1]} | ❓ |")
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)
            embed.set_field_at(0, name="Results", value=f"| {' | '.join(final_symbols)} |")
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)
            
            # Calculate winnings
            unique_symbols = len(set(final_symbols))
            if unique_symbols == 1:  # All three match
                symbol = final_symbols[0]
                multiplier = symbols[symbol]["multiplier"]
                gross_win = bet * multiplier
                tax_amount = int(gross_win * 0.05)  # 5% tax
                winnings = gross_win - tax_amount
                result = f"🎉 JACKPOT! Triple {symbols[symbol]['name']}! 🎉"
            elif unique_symbols == 2:  # Two match
                winnings = bet * 2
                tax_amount = int(winnings * 0.05)  # 5% tax
                winnings -= tax_amount
                result = "🎈 Two of a kind! 🎈"
            else:  # No matches
                winnings = 0
                tax_amount = 0
                result = "😢 No match!"
                    
            # Update balances
            if winnings > 0:
                self.currency[user_id] += winnings
                # House gets the tax
                house_id = str(self.bot.user.id)
                if house_id not in self.currency:
                    self.currency[house_id] = 0
                self.currency[house_id] += tax_amount
            else:
                # Player loses bet
                self.currency[user_id] -= bet
                # House gets the loss
                house_id = str(self.bot.user.id)
                if house_id not in self.currency:
                    self.currency[house_id] = 0
                self.currency[house_id] += bet

            # Save changes
            self.save_currency()
            
            # Get new balance
            new_balance = await self.get_balance(user_id)
            
            # Final embed
            final_embed = discord.Embed(
                title="🎰 SLOT MACHINE 🎰", 
                color=discord.Color.green() if winnings > 0 else discord.Color.red()
            )
            
            final_embed.add_field(
                name=result, 
                value=f"| {' | '.join(final_symbols)} |",
                inline=False
            )
            
            if winnings > 0:
                win_text = f"+<:goldpoints:1319902464115343473> {self.format_amount(winnings)}"
                if tax_amount > 0:
                    win_text += f"\nHouse Tax: <:goldpoints:1319902464115343473> {self.format_amount(tax_amount)} (5%)"
                final_embed.add_field(
                    name="You Won!", 
                    value=win_text,
                    inline=False
                )
            else:
                final_embed.add_field(
                    name="You Lost!", 
                    value=f"-<:goldpoints:1319902464115343473> {self.format_amount(bet)}", 
                    inline=False
                )
                
            final_embed.add_field(
                name="New Balance", 
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(new_balance)}", 
                inline=False
            )
            
            await msg.edit(embed=final_embed)
            
            # Flashy effects for big wins
            if winnings >= bet * 10:  # For really big wins
                for _ in range(3):
                    final_embed.color = discord.Color.gold()
                    await msg.edit(embed=final_embed)
                    await asyncio.sleep(0.3)
                    final_embed.color = discord.Color.green()
                    await msg.edit(embed=final_embed)
                    await asyncio.sleep(0.3)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")




    


async def setup(bot):
    await bot.add_cog(Economy(bot))
