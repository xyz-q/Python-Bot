import discord
from discord.ext import commands
from discord.ui import View, Button
import json
from typing import List
import math
import random
import asyncio
import typing
from functools import wraps
from discord.ext import commands
from typing import List
import math
from discord.ui import View, Button


def transaction_limit():
    async def predicate(ctx):
        try:
            # Get command arguments
            args = ctx.message.content.split()
            
            # Skip if no arguments
            if len(args) <= 1:
                return True
                
            # Try to find and parse amount from arguments
            amount = None
            for arg in args[1:]:
                try:
                    # Remove any currency symbols/characters
                    cleaned_arg = arg.strip('$,k,m,b,K,M,B')
                    # Try converting to number
                    if 'k' in arg.lower():
                        amount = float(cleaned_arg) * 1000
                    elif 'm' in arg.lower():
                        amount = float(cleaned_arg) * 1000000
                    elif 'b' in arg.lower():
                        amount = float(cleaned_arg) * 1000000000
                    else:
                        amount = float(cleaned_arg)
                    break
                except ValueError:
                    continue

            # If no valid amount found, let command handle it
            if amount is None:
                return True

            # Check limits
            MIN_LIMIT = 5_000_000  # 5M
            MAX_LIMIT = 5_000_000_000  # 5B

            if amount < MIN_LIMIT:
                await ctx.send(f"❌ Amount too low! Minimum amount is 5M")
                return False
            
            if amount > MAX_LIMIT:
                await ctx.send(f"❌ Amount too high! Maximum amount is 5B")
                return False

            return True

        except Exception as e:
            print(f"Transaction limit check error: {e}")
            return True

    return commands.check(predicate)

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
    MIN_TRANSACTION_AMOUNT = 50_000_000  # 50M minimum
    MAX_TRANSACTION_AMOUNT = 5_000_000_000  # 5B maximum
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
        if amount >= 10000000000:  # 10B+
            billions = amount / 1000000000
            return f"{int(billions):,}B"
        elif amount >= 1000000:  # Millions
            millions = amount / 1000000
            return f"{int(millions):,}M"
        elif amount >= 1000:  # Thousands
            thousands = amount / 1000
            return f"{int(thousands):,}K"
        return f"{int(amount):,}"




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
    @commands.has_permissions(administrator=True)
    async def balancelist(self, ctx):
        await ctx.message.delete()
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
    # Wait 20 seconds then delete the message
        await asyncio.sleep(20)
        try:
            await message.delete()
        except discord.NotFound:
            pass  # Message was already deleted
        except discord.Forbidden:
            pass 
    

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
    @commands.is_owner()
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
    @commands.is_owner()
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


    @commands.command(aliases=['send'])
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
                title="<:seeds:1326024477145956433> Staking Commands",
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
        try:
            if amount is None or rsn is None:
                await ctx.send("❌ Please provide both amount and RSN!\nUsage: `,deposit <amount> <rsn>`\nExample: `,deposit 100M Zezima`")
                return

            # Parse and validate amount
            try:
                parsed_amount = self.parse_amount(amount)
                # Add minimum and maximum limit checks
                if parsed_amount < self.MIN_TRANSACTION_AMOUNT:
                    await ctx.send(f"❌ Minimum deposit amount is <:goldpoints:1319902464115343473> {self.format_amount(self.MIN_TRANSACTION_AMOUNT)}!")
                    return
                if parsed_amount > self.MAX_TRANSACTION_AMOUNT:
                    await ctx.send(f"❌ Maximum deposit amount is <:goldpoints:1319902464115343473> {self.format_amount(self.MAX_TRANSACTION_AMOUNT)}!")
                    return
                formatted_amount = self.format_amount(parsed_amount)
            except ValueError:
                await ctx.send("❌ Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B)")
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
        try:
            if amount is None or rsn is None:
                await ctx.send("❌ Please provide both amount and RSN!\nUsage: `,withdraw <amount> <rsn>`\nExample: `,withdraw 100M Zezima`")
                return

            # Parse and validate amount
            try:
                parsed_amount = self.parse_amount(amount)
                # Add minimum and maximum limit checks
                if parsed_amount < self.MIN_TRANSACTION_AMOUNT:
                    await ctx.send(f"❌ Minimum withdrawal amount is <:goldpoints:1319902464115343473> {self.format_amount(self.MIN_TRANSACTION_AMOUNT)}!")
                    return
                if parsed_amount > self.MAX_TRANSACTION_AMOUNT:
                    await ctx.send(f"❌ Maximum withdrawal amount is <:goldpoints:1319902464115343473> {self.format_amount(self.MAX_TRANSACTION_AMOUNT)}!")
                    return
                formatted_amount = self.format_amount(parsed_amount)
            except ValueError:
                await ctx.send("❌ Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B)")
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
    

    @commands.command(name="pvpflip", aliases=["flip", "challenge", "cf"])
    @transaction_limit()
    async def pvpflip(self, ctx, opponent: discord.Member = None, bet: str = None):
        """Challenge another player to a coin flip"""
        try:
            if opponent is None or bet is None:
                await ctx.send("Please specify your opponent and bet amount! Example: ,challenge @player 1000")
                return

            # Can't challenge yourself
            if opponent.id == ctx.author.id:
                await ctx.send("You cannot challenge yourself!")
                return

            # Parse bet amount
            try:
                bet_amount = self.parse_amount(bet)
            except ValueError:
                await ctx.send("Invalid bet amount! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B, 1T)")
                return

            if bet_amount <= 0:
                await ctx.send("Bet amount must be positive!")
                return

            # Calculate house tax (5%)
            house_tax = int(bet_amount * 0.05)
            win_amount = bet_amount - house_tax

            # Check challenger's balance
            challenger_id = str(ctx.author.id)
            challenger_balance = await self.get_balance(challenger_id)

            # Check opponent's balance
            opponent_id = str(opponent.id)
            opponent_balance = await self.get_balance(opponent_id)

            # House ID (replace with your actual house account ID)
            house_id = "HOUSE_ACCOUNT_ID"

            # Verify both players have enough balance
            if challenger_balance < bet_amount:
                await ctx.send(f"You don't have enough balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(challenger_balance)}")
                return

            if opponent_balance < bet_amount:
                await ctx.send(f"{opponent.name} doesn't have enough balance! Their balance: <:goldpoints:1319902464115343473> {self.format_amount(opponent_balance)}")
                return

            # Create challenge embed with tax info
            challenge_embed = discord.Embed(
                title="🎲 PvP Coin Flip Challenge",
                description=f"{ctx.author.mention} has challenged {opponent.mention} to a coin flip!",
                color=discord.Color.gold()
            )
            
            challenge_embed.add_field(
                name="Bet Amount",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(bet_amount)}",
                inline=False
            )
            
            challenge_embed.add_field(
                name="House Tax (-5%)",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(house_tax)}",
                inline=False
            )
            
            challenge_embed.add_field(
                name="Winner Gets",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(win_amount)}",
                inline=False
            )

            # Create accept/decline buttons
            class ChallengeView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=30.0)
                    self.value = None
                    self.choice = None

                @discord.ui.button(label="Accept (Heads)", style=discord.ButtonStyle.green)
                async def heads(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == opponent.id:
                        self.value = True
                        self.choice = 'heads'
                        self.stop()

                @discord.ui.button(label="Accept (Tails)", style=discord.ButtonStyle.green)
                async def tails(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == opponent.id:
                        self.value = True
                        self.choice = 'tails'
                        self.stop()

                @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
                async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == opponent.id:
                        self.value = False
                        self.stop()

            # Send challenge and wait for response
            view = ChallengeView()
            challenge_msg = await ctx.send(embed=challenge_embed, view=view)

            # Wait for opponent's response
            await view.wait()

            if view.value is None:
                await challenge_msg.edit(content="Challenge timed out!", embed=None, view=None)
                return
            elif not view.value:
                await challenge_msg.edit(content="Challenge declined!", embed=None, view=None)
                return

            # Determine result
            import secrets
            result = 'heads' if secrets.randbelow(2) == 0 else 'tails'
            
            # Determine winner
            winner_id = challenger_id if result != view.choice else opponent_id
            loser_id = opponent_id if result != view.choice else challenger_id
            winner = ctx.author if winner_id == challenger_id else opponent
            loser = opponent if winner_id == challenger_id else ctx.author

            # Update balances with house tax
            self.currency[winner_id] = self.currency.get(winner_id, 0) + win_amount
            self.currency[loser_id] = self.currency.get(loser_id, 0) - bet_amount
            self.currency[house_id] = self.currency.get(house_id, 0) + house_tax

            # Save changes
            self.save_currency()

            # Create result embed
            result_embed = discord.Embed(
                title="🎲 PvP Coin Flip Result",
                color=discord.Color.green()
            )
            
            result_embed.add_field(
                name="The Coin Landed On",
                value=f"**{result.upper()}**",
                inline=False
            )
            
            result_embed.add_field(
                name="Winner",
                value=f"{winner.mention} (+{self.format_amount(win_amount)})",
                inline=False
            )
            
            result_embed.add_field(
                name="Loser",
                value=f"{loser.mention} (-{self.format_amount(bet_amount)})",
                inline=False
            )
            
            result_embed.add_field(
                name="House Tax",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(house_tax)}",
                inline=False
            )

            await challenge_msg.edit(content=None, embed=result_embed, view=None)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command(name="gamble", aliases=["slot", "slots"])
    @transaction_limit()
    async def gamble(self, ctx, amount: str):
        try:
            # Parse bet amount
            bet = self.parse_amount(amount)
            user_id = str(ctx.author.id)
            house_id = str(self.bot.user.id)
            user_balance = await self.get_balance(user_id)
            
            if bet <= 0:
                await ctx.send("You must bet at least 1 coin!")
                return
                    
            if bet > user_balance:
                await ctx.send(f"You don't have enough coins! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(user_balance)}")
                return

            # Define slot machine symbols with weights and multipliers (total weight = 100)
            symbols = {
                "💎": {"weight": 1, "multiplier": 50, "name": "Diamond"},     # 1%
                "🎰": {"weight": 2, "multiplier": 15, "name": "Jackpot"},    # 2%
                "7️⃣": {"weight": 7, "multiplier": 7, "name": "Seven"},       # 7%
                "🍀": {"weight": 15, "multiplier": 3, "name": "Clover"},     # 15%
                "⭐": {"weight": 35, "multiplier": 1.5, "name": "Star"},      # 35%
                "🎲": {"weight": 40, "multiplier": 0.8, "name": "Dice"}      # 40%
            }

            # Create weighted symbol list
            weighted_symbols = []
            for symbol, data in symbols.items():
                weighted_symbols.extend([symbol] * data["weight"])
            
            # Create and send initial embed
            embed = discord.Embed(title="🎰 SLOT MACHINE 🎰", color=discord.Color.gold())
            embed.add_field(name="Spinning...", value="| ❓ | ❓ | ❓ |")
            embed.set_footer(text=f"Balance: {self.format_amount(user_balance)} GP")
            msg = await ctx.send(embed=embed)

            # Generate final results with near-miss logic
            async def generate_results():
                # Only 5% chance to even attempt a match
                if random.random() < 0.15:  # 5% chance for potential match
                    if random.random() < 0.15:  # 15% of that 5% (0.75% total) for three of a kind
                        symbol = random.choice(weighted_symbols)
                        return [symbol, symbol, symbol]
                    else:  # Rest of the 5% (4.25% total) for two of a kind
                        symbol = random.choice(weighted_symbols)
                        third = random.choice([s for s in weighted_symbols if s != symbol])
                        return [symbol, symbol, third]
                else:  # 95% chance for completely random results
                    results = []
                    for _ in range(3):
                        random.shuffle(weighted_symbols)
                        results.append(random.choice(weighted_symbols))
                    return results

            final_symbols = await generate_results()

            # Spinning animation
            for reel in range(3):
                for _ in range(2):  # Two fake spins per reel
                    temp_symbols = [
                        random.choice(weighted_symbols) if i == reel 
                        else (final_symbols[i] if i < reel else '❓') 
                        for i in range(3)
                    ]
                    embed.set_field_at(0, name="Spinning...", 
                                    value=f"| {' | '.join(temp_symbols)} |")
                    await msg.edit(embed=embed)
                    await asyncio.sleep(0.5)

                # Show final symbol for this reel
                temp_symbols = [final_symbols[i] if i <= reel else '❓' for i in range(3)]
                embed.set_field_at(0, name="Spinning..." if reel < 2 else "Results", 
                                value=f"| {' | '.join(temp_symbols)} |")
                await msg.edit(embed=embed)
                await asyncio.sleep(0.5)

            # Calculate matches and winnings
            symbol_counts = {}
            for symbol in final_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            max_matches = max(symbol_counts.values())

            # Calculate winnings based on matches
            if max_matches == 3:  # Three of a kind (rare, ~0.75% chance)
                symbol = max(symbol_counts, key=symbol_counts.get)
                multiplier = symbols[symbol]["multiplier"]
                gross_win = bet * multiplier
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                result = f"🎉 JACKPOT! Triple {symbols[symbol]['name']}! 🎉"
            
            elif max_matches == 2:  # Two of a kind (uncommon, ~4.25% chance)
                matching_symbol = [s for s, count in symbol_counts.items() if count == 2][0]
                base_multiplier = symbols[matching_symbol]["multiplier"]
                multiplier = base_multiplier * 0.4  # 40% of original multiplier
                gross_win = int(bet * multiplier)
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                result = f"🎈 Double {symbols[matching_symbol]['name']}! 🎈"
            

            else:
                winnings = 0
                tax_amount = 0
                result = "No match!"

            # Update balances
            if winnings > 0:
                if house_id not in self.currency:
                    self.currency[house_id] = 0
                    
                if self.currency[house_id] < winnings:
                    await ctx.send("The house doesn't have enough balance to pay out! Try a smaller bet.")
                    return

                self.currency[user_id] = self.currency.get(user_id, 0) + winnings
                self.currency[house_id] += tax_amount
                self.currency[house_id] -= winnings
            else:
                self.currency[user_id] = self.currency.get(user_id, 0) - bet
                self.currency[house_id] = self.currency.get(house_id, 0) + bet

            # Save changes
            self.save_currency()

            # Create result embed
            result_embed = discord.Embed(
                title="🎰 SLOT MACHINE RESULTS 🎰",
                color=discord.Color.green() if winnings > 0 else discord.Color.red()
            )
            
            result_embed.add_field(
                name=result,
                value=f"| {' | '.join(final_symbols)} |",
                inline=False
            )
            
            result_embed.add_field(
                name="Outcome",
                value=f"Bet: {self.format_amount(bet)}\n"
                    f"Win: {self.format_amount(winnings)}\n"
                    f"Tax: {self.format_amount(tax_amount)}",
                inline=False
            )
            
            result_embed.set_footer(
                text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} GP"
            )

            await msg.edit(embed=result_embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")




    @commands.command(aliases=["flowe", "flowers"])
    @transaction_limit()
    async def flower(self, ctx, bet_amount: str = None):
        if bet_amount is None:
            # Create an embed for the flower command help/info
            help_embed = discord.Embed(
                title="<:seeds:1326024477145956433> Flower Game Information",
                description="Welcome to the Flower Staking Game!",
                color=discord.Color.gold()
            )
            
            # Add fields explaining the flowers and their values
            help_embed.add_field(
                name="Regular Flowers",
                value=(
                    "<:rainbow:1326018658648195103> = 0\n"
                    "<:pastel:1326018646098706564> = 0\n"
                    "<:red:1326018733826773023> = 2\n"
                    "<:purple:1326018686817009734> = 3\n"
                    "<:yellow:1326018708136792085> = 4\n"
                    "<:blue:1326018721730396190> = 5\n"
                    "<:orange:1326018671763521557> = 6"
                ),
                inline=True
            )
            
            help_embed.add_field(
                name="Special Flowers",
                value=(
                    "<:white:1326018610719756340> = Instant Win!\n"
                    "<:black:1326018632739721327> = Instant Loss!"
                ),
                inline=True
            )
            
            help_embed.add_field(
                name="How to Play",
                value=(
                    "• Use `,flower <bet amount>` to play!\n• Get a higher total than the banker to win!\n"
                    "• Numbers over 10 reset (eg: 12 becomes 2)"
                ),
                inline=False
            )
            
            await ctx.send(embed=help_embed)
            return

        # If bet_amount is provided, continue with the existing game logic
        try:
            # Your existing game code here...
            house_id = str(self.bot.user.id)
            if house_id not in self.currency:
                self.currency[house_id] = 0           
            # Flowers with their values and weights (odds)
            flowers = {
                "<:rainbow:1326018658648195103>": {"value": 0, "weight": 12},    
                "<:pastel:1326018646098706564>": {"value": 0, "weight": 12},    
                "<:red:1326018733826773023>": {"value": 2, "weight": 15},    
                "<:blue:1326018721730396190>": {"value": 5, "weight": 15},    
                "<:yellow:1326018708136792085>": {"value": 4, "weight": 15},   
                "<:purple:1326018686817009734>": {"value": 3, "weight": 15},    
                "<:orange:1326018671763521557>": {"value": 6, "weight": 15},    
                "<:white:1326018610719756340>": {"value": "WIN", "weight": 0.1},  
                "<:black:1326018632739721327>": {"value": "LOSE", "weight": 0.2}  
            }

            # Validate bet amount first
            amount = self.parse_amount(bet_amount)
            if amount <= 0:
                await ctx.send("Please enter a valid bet amount!")
                return

            # Check if user has enough balance
            user_id = str(ctx.author.id)
            if user_id not in self.currency:
                self.currency[user_id] = 0
            
            if self.currency[user_id] < amount:
                await ctx.send("You don't have enough balance for this bet!")
                return

            def calculate_total(numbers):
                """Calculate total, implementing the 10+ reset rule after each addition"""
                print(f"Received numbers to calculate: {numbers}")  # Debug print
                running_total = 0
                for num in numbers:
                    if isinstance(num, int):
                        print(f"Adding {num} to {running_total}")  # Debug print
                        running_total += num
                        running_total %= 10
                        print(f"After mod 10: {running_total}")  # Debug print
                
                print(f"Final total: {running_total}")  # Debug print
                return running_total



            def needs_third_card(total):
                """Determine if a third card is needed (5 or below)"""
                return total <= 5

            def pick_flower():
                """Pick a random flower based on weights"""
                flower_list = list(flowers.keys())
                weights = [flowers[f]["weight"] for f in flower_list]
                chosen_flower = random.choices(flower_list, weights=weights, k=1)[0]
                return chosen_flower, flowers[chosen_flower]["value"]

            # Initialize game state with placeholder seeds
            player_hand = []
            banker_hand = []
            player_flowers = ["<:seeds:1326024477145956433>"] * 3  # 3 placeholder seeds
            banker_flowers = ["<:seeds:1326024477145956433>"] * 3  # 3 placeholder seeds

            # Create initial embed showing all placeholders
            game_embed = discord.Embed(title="<:seeds:1326024477145956433> Flower Staking Game", color=discord.Color.gold())
            game_embed.add_field(
                name="Your Bet", 
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                inline=False
            )
            game_embed.add_field(
                name="Player's Hand", 
                value=f"{''.join(player_flowers)}", 
                inline=False
            )
            game_embed.add_field(
                name="Banker's Hand", 
                value=f"{''.join(banker_flowers)}", 
                inline=False
            )
            game_message = await ctx.send(embed=game_embed)

            # Player's first two cards
            game_embed.add_field(name="Status", value="Drawing player's cards...", inline=False)
            await game_message.edit(embed=game_embed)
            await asyncio.sleep(1)

            for i in range(2):
                p_flower, p_value = pick_flower()
                if p_value == "WIN":
                    await ctx.send(f"{ctx.author.mention} got White Flower! Instant Win! 💰")
                    self.currency[user_id] += amount
                    self.save_currency()
                    return
                elif p_value == "LOSE":
                    await ctx.send(f"{ctx.author.mention} got Black Flower! House Wins! 💀")
                    self.currency[user_id] -= amount
                    self.save_currency()
                    return
                
                player_hand.append(p_value)
                player_flowers[i] = p_flower  # Replace placeholder with actual flower
                
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Player's Hand", 
                    value=f"{''.join(player_flowers)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Banker's Hand", 
                    value=f"{''.join(banker_flowers)}", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

            # Check if player needs third card
            player_total = calculate_total(player_hand)
            if needs_third_card(player_total):
                game_embed.add_field(
                    name="Status", 
                    value="Drawing third card for player...", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

                p_flower, p_value = pick_flower()
                if p_value == "WIN":
                    await ctx.send(f"{ctx.author.mention} got White Flower! Instant Win! 💰")
                    self.currency[user_id] += amount
                    self.save_currency()
                    return
                elif p_value == "LOSE":
                    await ctx.send(f"{ctx.author.mention} got Black Flower! House Wins! 💀")
                    self.currency[user_id] -= amount
                    self.save_currency()
                    return
                
                player_hand.append(p_value)
                player_flowers[2] = p_flower
                player_total = calculate_total(player_hand)  # Recalculate total after third card
            # Replace third placeholder
                
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Player's Hand", 
                    value=f"{''.join(player_flowers)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Banker's Hand", 
                    value=f"{''.join(banker_flowers)}", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

            # Now banker's turn
            game_embed.add_field(name="Status", value="Drawing banker's cards...", inline=False)
            await game_message.edit(embed=game_embed)
            await asyncio.sleep(1)

            # Banker's two cards
            for i in range(2):
                b_flower, b_value = pick_flower()
                banker_hand.append(b_value)
                banker_flowers[i] = b_flower  # Replace placeholder with actual flower
                
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Player's Hand", 
                    value=f"{''.join(player_flowers)} = {player_total}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Banker's Hand", 
                    value=f"{''.join(banker_flowers)}", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

            # Check if banker needs third card
            banker_total = calculate_total(banker_hand)
            if needs_third_card(banker_total):
                game_embed.add_field(
                    name="Status", 
                    value="Drawing third card for banker...", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

                b_flower, b_value = pick_flower()
                banker_hand.append(b_value)
                banker_flowers[2] = b_flower  # Replace third placeholder
                banker_total = calculate_total(banker_hand)

                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Player's Hand", 
                    value=f"{''.join(player_flowers)} = {player_total}", 
                    inline=False
                )
                game_embed.add_field(
                    name="Banker's Hand", 
                    value=f"{''.join(banker_flowers)} = {banker_total}", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)



            # Final result embed
            final_embed = discord.Embed(title="<:seeds:1326024477145956433> Flower Staking Game", color=discord.Color.gold())
            final_embed.add_field(
                name="Your Bet", 
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                inline=False
            )
            final_embed.add_field(
                name="Player's Hand", 
                value=f"{''.join(player_flowers)} = {player_total}", 
                inline=False
            )
            final_embed.add_field(
                name="Banker's Hand", 
                value=f"{''.join(banker_flowers)} = {banker_total}", 
                inline=False
            )
            #-------------------------------------------    
    # Determine winner and update balances
            if player_total == 9 and banker_total == 9:
                # Tie on 9s, banker wins
                final_embed.add_field(
                    name="Result", 
                    value="Double 9s! Banker wins! <a:xdd:1221066292631568456>", 
                    inline=False
                )
                self.currency[user_id] -= amount
                self.currency[house_id] += amount  # Add to house balance
            elif player_total > banker_total:
                # Player wins
                winnings = amount * 2  # Double the bet
                tax_amount = int(winnings * 0.05)  # 5% tax
                net_winnings = winnings - tax_amount
                
                self.currency[user_id] += net_winnings
                self.currency[house_id] -= winnings  # House pays winnings
                self.currency[house_id] += tax_amount  # House keeps the tax
                final_embed.add_field(
                    name="Result", 
                    value=f"You win! <a:MUGA:1178140574570790954>\nWinnings: {self.format_amount(net_winnings)} (After 5% tax)", 
                    inline=False
                )
            elif banker_total > player_total:
                # Banker wins
                self.currency[user_id] -= amount
                self.currency[house_id] += amount  # Add to house balance
                final_embed.add_field(
                    name="Result", 
                    value="Banker wins! <a:xdd:1221066292631568456>", 
                    inline=False
                )
            else:
                
                final_embed.add_field(
                    name="Result", 
                    value="Tie! It's a push. <a:aware:1255561720810831912>", 
                    inline=False
                )

            # Save the updated currency values
            self.save_currency()
            await game_message.edit(embed=final_embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")






    


async def setup(bot):
    await bot.add_cog(Economy(bot))
