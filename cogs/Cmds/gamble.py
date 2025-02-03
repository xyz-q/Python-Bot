import discord
from discord.ext import commands, tasks
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
from pathlib import Path
import functools
from datetime import datetime, timedelta, time
import copy
import typing

class DayInput(discord.ui.Modal, title="Custom Time Input"):
    days = discord.ui.TextInput(
        label='Enter time in days',
        placeholder='Enter a number between 1 and 25',
        min_length=1,
        max_length=2,
        required=True
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            days = float(self.days.value)
            if days < 1:
                await interaction.response.send_message("Time must be at least 1 day!", ephemeral=True)
                return
            if days > 25:
                await interaction.response.send_message("Time cannot exceed 25 days!", ephemeral=True)
                return
            
            self.view.value = timedelta(days=days)
            self.view.disable_all_buttons()
            await interaction.response.edit_message(view=self.view)
            self.view.stop()
            
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True)
            
def has_account():
    message_sent = set()
    
    async def predicate(ctx):
        user_id = str(ctx.author.id)
        
        # Load TOS acceptance data from JSON
        try:
            with open('.json/tos.json', 'r') as f:
                tos_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create file if it doesn't exist
            tos_data = {}
            os.makedirs('data', exist_ok=True)
            with open('.json/tos.json', 'w') as f:
                json.dump(tos_data, f)

        # Check if user has accepted TOS
        if user_id in tos_data:
            return True
            
        # Create unique key for this command invocation
        message_key = f"{ctx.message.id}"
        
        # Only send message if we haven't sent one for this command invocation
        if message_key not in message_sent:
            message_sent.add(message_key)
            
            embed = discord.Embed(
                title="You haven't read the terms of service yet!",
                description="",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Terms & Conditions",
                value="1. You must be __**21**__ **years** or older to use our services.\n"
                    "2. ***ANY*** form of exploitation will result in a __**PERMANENT**__ blacklist.\n"
                    "3. This is for __***entertainment***__ purposes only. **Do not** expect to make money.\n"
                    "4. ***ALL*** transactions are final. Please contact staff if you have an issue.\n"
            )
            embed.add_field(
                name="Privacy Notice",
                value="• We track gambling statistics and transaction history\n"
                    "• Your data is used for feature improvement and enhancing user experience.\n"
                    "• Your activity may be logged for security purposes\n\n"
                    "   Please use `,accept` if you agree to these.",                    
                inline=False
            )
            embed.set_footer(text="    2025 N.I.C.E™ Inc")
            await ctx.send(embed=embed)
            await asyncio.sleep(3)
            
            # Clean up after a delay
            message_sent.discard(message_key)
            
        return False
            
    return commands.check(predicate)







user_locks = {}
def user_lock():
    """Prevents a user from running multiple commands at once"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if user_locks.get(ctx.author.id):
                await ctx.message.delete()
                cooldown =await ctx.send(f"<:remove:1328511957208268800> {ctx.author.mention} Please wait for your current command to finish!")
                await asyncio.sleep(3)
                await cooldown.delete()
                return
            
            try:
                user_locks[ctx.author.id] = True
                return await func(self, ctx, *args, **kwargs)
            finally:
                user_locks[ctx.author.id] = False
        return wrapper
    return decorator


class GambleLimits:
    def __init__(self):
        self.default_min = 500_000
        self.default_max = 100_000_000
        self.limits_file = ".json/limits.json"
        self.current_min = self.default_min
        self.current_max = self.default_max
        self.load_limits()

    def format_amount(self, amount):
        # Convert to integer if it's a whole number
        if amount.is_integer():
            return int(amount)
        return amount

    def load_limits(self):
        try:
            with open(self.limits_file, 'r') as f:
                limits = json.load(f)
                self.current_min = self.format_amount(float(limits.get('min', self.default_min)))
                self.current_max = self.format_amount(float(limits.get('max', self.default_max)))
        except FileNotFoundError:
            self.save_limits()

    def save_limits(self):
        with open(self.limits_file, 'w') as f:
            json.dump({'min': self.current_min, 'max': self.current_max}, f)

# Create a global instance
limits_manager = GambleLimits()



def transaction_limit():
    # Store the last message time for each user
    last_message = {}
    
    async def predicate(ctx):
        try:
            # Get current user ID
            user_id = ctx.author.id
            current_time = datetime.now()
            
            # Check if we've sent a message recently (within 1 second)
            if user_id in last_message:
                if current_time - last_message[user_id] < timedelta(seconds=1):
                    return False
                
            args = ctx.message.content.split()
            
            if len(args) <= 1:
                return True
                
            amount = None
            for arg in args[1:]:
                try:
                    cleaned_arg = arg.strip('$,k,m,b,t,K,M,B,T')
                    if 'k' in arg.lower():
                        amount = float(cleaned_arg) * 1000
                    elif 'm' in arg.lower():
                        amount = float(cleaned_arg) * 1000000
                    elif 'b' in arg.lower():
                        amount = float(cleaned_arg) * 1000000000
                    elif 't' in arg.lower():
                        amount = float(cleaned_arg) * 1000000000000
                    else:
                        amount = float(cleaned_arg)
                    break
                except ValueError:
                    continue

            if amount is None:
                return True

            if amount < limits_manager.current_min:
                last_message[user_id] = current_time
                await ctx.message.delete()
                await ctx.send(
                    f"Amount too low! Minimum amount is {limits_manager.current_min:,} <:goldpoints:1319902464115343473>",
                    delete_after=3
                )
                return False
            
            elif amount > limits_manager.current_max:
                last_message[user_id] = current_time
                await ctx.message.delete()
                await ctx.send(
                    f"Amount too high! Maximum amount is {limits_manager.current_max:,} <:goldpoints:1319902464115343473>",
                    delete_after=3
                )
                return False

            return True

        except Exception as e:
            print(f"Transaction limit check error: {e}")
            return True

    return commands.check(predicate)




import functools
import json

import os

from functools import wraps

def confirm_bet():
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, amount=None, *args, **kwargs):
            if amount is None:
                # If no amount is provided, proceed with the original function
                return await func(self, ctx, amount, *args, **kwargs)

            # Step 1: Convert the amount using your existing parse_amount method
            try:
                amount = self.parse_amount(str(amount))
                print(f"Converted amount: {amount}")

            except ValueError:
                await ctx.send("<:remove:1328511957208268800> Confirmation error: Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B)", delete_after=10)
                return None

            # Step 2: Check if the amount is valid (positive and within user balance)
            if amount <= 0:
                await ctx.send("<:remove:1328511957208268800> Confirmation error:  Amount must be positive!", delete_after=10)
                return None

            balance = await self.get_balance(ctx.author.id)
            print(f"User balance: {balance}")
            if amount > balance:
                await ctx.message.delete()
                await ctx.send(f"<:remove:1328511957208268800> Insufficient balance! Your balance <:goldpoints:1319902464115343473> {self.format_amount(balance)}\n\n Use ,deposit <amount> <rsn> to add more.", delete_after=10)
                return None
            # Step 3: If the amount exceeds the threshold, trigger the confirmation
            if amount >= self.CONFIRMATION_THRESHOLD:
                print(f"Amount exceeds threshold: {self.CONFIRMATION_THRESHOLD}")
                view = BetConfirmation()  # Assuming this is a button or modal view
                message = await ctx.send(
                    f"⚠️ Are you sure you want to use {self.format_amount(amount)} <:goldpoints:1319902464115343473>?", 
                    view=view
                )

                await view.wait()

                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

                if view.value is None:
                    await ctx.send("⚠️ Confirmation timed out!", delete_after=10)
                    return None
                elif view.value is False:
                    await ctx.send("<:remove:1328511957208268800> Cancelled!", delete_after=10)
                    return None

                print("Confirmed!")

            # Step 4: If the amount is below threshold or confirmed, proceed with the command
            return await func(self, ctx, amount, *args, **kwargs)

        return wrapper
    return decorator




class TransactionPaginator(discord.ui.View):
    def __init__(self, transactions, ctx, user_id, display_name):
        super().__init__(timeout=20)
        self.transactions = transactions
        self.ctx = ctx
        self.user_id = user_id
        self.display_name = display_name
        self.current_page = 0
        self.items_per_page = 5
        self.total_pages = max(1, (len(transactions) + self.items_per_page - 1) // self.items_per_page)

    @discord.ui.button(label="First", style=discord.ButtonStyle.grey)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return
        self.current_page = 0
        await interaction.response.edit_message(embed=self.get_page_embed())

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return
        self.current_page = max(0, self.current_page - 1)
        await interaction.response.edit_message(embed=self.get_page_embed())

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await interaction.response.edit_message(embed=self.get_page_embed())

    @discord.ui.button(label="Last", style=discord.ButtonStyle.grey)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return
        self.current_page = self.total_pages - 1
        await interaction.response.edit_message(embed=self.get_page_embed())

    def get_page_embed(self):
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_transactions = self.transactions[start_idx:end_idx]

        embed = discord.Embed(
            title=f"Transactions for {self.display_name} ", 
            color=discord.Color.gold()
        )

        for trans in reversed(page_transactions):
            transaction = trans["transaction"]
            bet = transaction.get("bet", 0)
            amount = transaction.get("amount", 0)
            trans_type = transaction.get("type", "game")
            
            if trans_type == "game":
                emoji = "<:upward:1328517849861324931> " if amount > 0 else "<:downward:1328517880882532372> "
                bet_str = f"Bet: {abs(bet):,}\n" if bet else ""
                amount_str = f"Result: {'+'if amount > 0 else '-'}{abs(amount):,} <:goldpoints:1319902464115343473>"
            elif trans_type == "add":
                emoji = "<:add:1328511998647861390>"
                bet_str = ""
                amount_str = f"Added: +{abs(amount):,} <:goldpoints:1319902464115343473>"
            elif trans_type == "remove":
                emoji = "<:remove:1328511957208268800>"
                bet_str = ""
                amount_str = f"Withdrew: -{abs(amount):,} <:goldpoints:1319902464115343473> "
            elif trans_type == "transfer":
                emoji = "<:transfer:1328517050120929380>"
                bet_str = ""
                transfer_info = transaction.get("transfer_info", "Transferred")
                amount_str = f"{transfer_info}: {'+'if amount > 0 else ''}{abs(amount):,} <:goldpoints:1319902464115343473>"
            elif trans_type == "vault_deposit":
                emoji = "🏦"  # or use a custom emoji if you have one
                bet_str = ""
                amount_str = f"Deposited to vault: -{abs(amount):,} <:goldpoints:1319902464115343473>"
            elif trans_type == "vault_withdraw":
                emoji = "🏦"  # or use a custom emoji if you have one
                bet_str = ""
                amount_str = f"Withdrawn from vault: +{abs(amount):,} <:goldpoints:1319902464115343473>"
            
            embed.add_field(
                name=f"{emoji} {transaction['command'].title()}",
                value=f"{bet_str}{amount_str}\n"
                    f"Balance After: {transaction['final_balance']:,} <:goldpoints:1319902464115343473>\n"
                    f"Time: {trans['timestamp']}",
                inline=False
            )

        embed.set_footer(text=f"(Page {self.current_page + 1}/{self.total_pages})")
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This pagination menu is not for you!", ephemeral=True)
            return False
        self.message = interaction.message
        return True




class BetConfirmation(discord.ui.View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons after clicking
        for item in self.children:
            item.disabled = True
        
        self.value = True
        await interaction.response.edit_message(content="Confirmed!", view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons after clicking
        for item in self.children:
            item.disabled = True
            
        self.value = False
        await interaction.response.edit_message(content="Cancelled!", view=self)
        self.stop()        

class PaginationView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=30)
        self.embeds = embeds
        self.current_page = 0
        self.message = None

    async def on_timeout(self):
        """Deletes the message when the view times out (like 'Close' button)."""
        if self.message:  # ✅ Ensure the message exists
            try:
                await self.message.delete()  # ✅ Deletes the message after timeout
            except discord.NotFound:
                pass  # Message was already deleted
            except discord.HTTPException:
                pass  # Some other error (bot lacks permission, etc.)

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
    MIN_TRANSACTION_AMOUNT = 10_000_000  # 50M minimum
    MAX_DEPOSIT_AMOUNT = 2_000_000_000  # 2B maximum
    MAX_WITHDRAW_AMOUNT = 500_000_000  # 500M maximum
    def __init__(self, bot):
        self.admin_ids = [110927272210354176, 311612585524854805]
        self.bot = bot
        self.current_author = None
        self.currency = {}
        self.load_currency()
        self.balances = {}
        self.stats = {}
        self.load_stats()  
        self.admin_id = 110927272210354176
        if not hasattr(self, 'interest_task') or not self.interest_task.is_running():
            self.interest_task.start()

        

        self.CONFIRMATION_THRESHOLD = 75_000_000
        self.symbols = {
        "<:rosa:1323457812755644498>": {"weight": 1, "multiplier": 50, "name": "Jackpot"},
        "<:diamond:1328609035485970432>": {"weight": 3, "multiplier": 25, "name": "Diamond"}, 
        "<:cash:1328609314411384893>": {"weight": 7, "multiplier": 15, "name": "Cash"},          
        "<:bar:1328604287495831624>": {"weight": 10, "multiplier": 10, "name": "Bar"},   
        "<:seven:1328610655854661673>": {"weight": 15, "multiplier": 7, "name": "Seven"},     
        "<:bell:1328610673047109714>": {"weight": 17, "multiplier": 5, "name": "Bell"},     
        "<:cherries:1328604145749459036>": {"weight": 17, "multiplier": 3.5, "name": "Cherries"},    
        "<:grapes:1328603707390033921>": {"weight": 17, "multiplier": 2.5, "name": "Grapes"},
        "<:lemon:1328603669565935648>": {"weight": 17, "multiplier": 1.5, "name": "Lemon"},
        "<:orange:1328603878316441610>": {"weight": 17, "multiplier": 1, "name": "Orange"}        

}
        if not os.path.exists('logs'):
            os.makedirs('logs')

    def set_author(self, author):
        self.current_author = author

    def get_author(self):
        return self.current_author

    async def log_transaction(self, ctx, bet_amount, win_amount, final_balance, transaction_type="game", is_house=False):
        """Log a transaction for both users and house"""
        try:
            # If it's a house transaction, use special house ID and name
            if is_house:
                user_id = "HOUSE"
                user_name = "House"
            else:
                user_id = str(ctx.author.id)
                user_name = str(ctx.author)
            
            # Convert all amounts to integers
            bet_amount = int(bet_amount) if bet_amount else 0
            win_amount = int(win_amount) if win_amount else 0
            final_balance = int(final_balance)
            
            # Create transaction data
            transaction_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": {
                    "id": user_id,
                    "name": user_name
                },
                "transaction": {
                    "command": ctx.command.name if not is_house else "House Transaction",
                    "type": transaction_type,
                    "bet": bet_amount,
                    "amount": win_amount,
                    "final_balance": final_balance
                }
            }

            try:
                with open('logs/transactions.json', 'r') as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                logs = {"users": {}}

            if user_id not in logs["users"]:
                logs["users"][user_id] = {
                    "transactions": []
                }

            logs["users"][user_id]["transactions"].append(transaction_data)
            logs["users"][user_id]["transactions"] = logs["users"][user_id]["transactions"][-100:]

            with open('logs/transactions.json', 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            print(f"Logging error: {e}")



 





    async def confirm_large_bet(self, ctx, amount):
        if amount >= self.CONFIRMATION_THRESHOLD:
            view = BetConfirmation()
            msg = await ctx.send(
                f"⚠️ You are about to bet {self.format_amount(amount)}! Are you sure?",
                view=view
            )
            
            # Wait for confirmation
            await view.wait()
            await msg.delete()
            
            return view.value
        
        return True


    def load_stats(self):
        try:
            with open('.json/gambling_stats.json', 'r') as f:
                self.stats = json.load(f)
        except FileNotFoundError:
            self.stats = {}

    def save_stats(self):
        with open('.json/gambling_stats.json', 'w') as f:
            json.dump(self.stats, f, indent=4)

    def initialize_user_stats(self, user_id):
        if str(user_id) not in self.stats:
            self.stats[str(user_id)] = {
                "total_wagered": 0,
                "total_won": 0,
                "total_lost": 0,
                "biggest_win": 0,
                "games_played": 0
            }

    def update_stats(self, user_id, amount_wagered, amount_won):
        user_id = str(user_id)
        self.initialize_user_stats(user_id)
        
        # Convert amounts to integers
        try:
            amount_wagered = int(amount_wagered)
            amount_won = int(amount_won)
        except ValueError:
            amount_wagered = self.parse_amount(str(amount_wagered))
            amount_won = self.parse_amount(str(amount_won))

        # Update total wagered and games played
        self.stats[user_id]["total_wagered"] += amount_wagered
        self.stats[user_id]["games_played"] += 1
        
        # Calculate actual profit/loss from this game
        if amount_won > amount_wagered:  # Won
            profit = amount_won - amount_wagered
            self.stats[user_id]["total_won"] += profit
            if profit > self.stats[user_id]["biggest_win"]:
                self.stats[user_id]["biggest_win"] = profit
        else:  # Lost
            loss = amount_wagered
            self.stats[user_id]["total_lost"] += loss

        self.save_stats()

    @commands.command(name="accept")
    async def create_account(self, ctx):
        """Create a new account"""
        user_id = str(ctx.author.id)
        
        # Load TOS data
        try:
            with open('.json/tos.json', 'r') as f:
                tos_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            tos_data = {}
            os.makedirs('data', exist_ok=True)
            with open('.json/tos.json', 'w') as f:
                json.dump(tos_data, f)
        
        # Check if user already accepted TOS
        if user_id in tos_data:
            await ctx.send("You have already accepted the TOS!")
            return
        
        # Add user to TOS acceptance file
        tos_data[user_id] = {
            "accepted_at": str(discord.utils.utcnow()),
            "username": str(ctx.author)
        }
        
        # Save updated TOS data
        with open('.json/tos.json', 'w') as f:
            json.dump(tos_data, f, indent=4)
        
        # Create welcome embed
        embed = discord.Embed(
            title="<:add:1328511998647861390> Account Created!",
            description="Welcome to the staking community!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="",
            value="Here are some commands to get you started:\n"
                "• `,balance` - Check your balance\n"
                "• `,flower <bet>` - Flower Baccarat!\n"
                "• `,staking` - See all staking commands\n"
                "• `,vault` - Deposit/withdraw from the vault\n"
                "• `,stats` - View your gambling statistics\n",
            inline=False
        )
        embed.set_footer(text=f"{ctx.author.display_name} has accepted.", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)



    @has_account()
    @commands.command(name="transactions", aliases=['history', 'past'])
    
    async def view_transactions(self, ctx, user: typing.Union[discord.Member, str] = None):
        """View recent transactions for a user or house"""
        try:
            await ctx.message.delete()
            with open('logs/transactions.json', 'r') as f:
                logs = json.load(f)

            if user is None:
                target_user = ctx.author
                user_id = str(target_user.id)
                display_name = target_user.name
            elif isinstance(user, str) and user.lower() == "house":
                user_id = "HOUSE"
                display_name = "House"
            else:
                target_user = user
                user_id = str(target_user.id)
                display_name = target_user.name

            if user_id not in logs["users"]:
                await ctx.send("No transactions found!")
                return

            transactions = logs["users"][user_id]["transactions"]
            
            view = TransactionPaginator(
                transactions=transactions,
                ctx=ctx,
                user_id=user_id,
                display_name=display_name
            )
            
            message = await ctx.send(embed=view.get_page_embed(), view=view)
            view.message = message

        except Exception as e:
            await ctx.send("Error retrieving transactions.")
            print(f"Error: {e}")

    @commands.command()
    @commands.is_owner()
    async def clearcurrency(self, ctx):
        confirm_msg = await ctx.send("⚠️ Are you sure you want to clear all currency data? This action cannot be undone!\nReact with ✅ to confirm or ❌ to cancel.")
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message == confirm_msg

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                with open('./.json/currency.json', 'w') as f:
                    json.dump({}, f, indent=4)
                await ctx.send("✅ Currency data has been cleared successfully!")
            else:
                await ctx.send("❌ Operation cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("❌ Operation timed out.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while clearing the currency data: {str(e)}")

    @has_account()
    @commands.command(name="resetstats")
    @commands.is_owner()
    async def reset_stats(self, ctx, target: typing.Union[discord.Member, str] = None):
        """Reset statistics for a user or all users"""
        if target and not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset other users' stats!")
            return

        if isinstance(target, str) and target.lower() == "all":
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("Only administrators can reset all users' stats!")
                return

            # Store the number of users affected
            users_affected = len(self.stats)
            
            # Store some examples for the embed
            example_users = list(self.stats.keys())[:5]  # First 5 users
            
            # Reset all stats
            for user_id in self.stats:
                self.stats[user_id] = {
                    "total_wagered": 0,
                    "total_won": 0,
                    "total_lost": 0,
                    "biggest_win": 0,
                    "games_played": 0
                }
            
            self.save_stats()

            # Create embed for response
            embed = discord.Embed(
                title="Statistics Reset",
                description=f"Reset statistics for {users_affected} users",
                color=discord.Color.gold()
            )
            
            # Add sample users to embed
            if example_users:
                sample_users = "\n".join([f"<@{user_id}>" for user_id in example_users])
                if len(self.stats) > 5:
                    sample_users += "\n..."
                embed.add_field(
                    name="Sample Users Reset",
                    value=sample_users,
                    inline=False
                )

            await ctx.send(embed=embed)

        else:
            # Handle single user reset
            target_user = target or ctx.author
            user_id = str(target_user.id)
            
            # Reset the stats for the user
            self.stats[user_id] = {
                "total_wagered": 0,
                "total_won": 0,
                "total_lost": 0,
                "biggest_win": 0,
                "games_played": 0
            }
            
            self.save_stats()

            # Create embed for single user reset
            embed = discord.Embed(
                title="Statistics Reset",
                description=f"Statistics have been reset for {target_user.name}",
                color=discord.Color.gold()
            )
            
            await ctx.send(embed=embed)

    @reset_stats.error
    async def reset_stats_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("<:remove:1328511957208268800> Could not find that user!")
        elif isinstance(error, commands.BadUnionArgument):
            await ctx.send("<:remove:1328511957208268800> Invalid target! Use either a user mention or 'all'")

    @has_account()
    @commands.command(name="stats")
    async def show_stats(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        user_id = str(user.id)
        
        if user_id not in self.stats:
            await ctx.send("No gambling statistics found for this user.")
            return

        stats = self.stats[user_id]
        net_profit = stats["total_won"] - stats["total_lost"]
        
        embed = discord.Embed(title=f"Gambling Statistics for {user.name}", color=discord.Color.gold())
        embed.add_field(name="Total Wagered", value=f"${stats['total_wagered']:,}", inline=False)
        embed.add_field(name="Total Won", value=f"${stats['total_won']:,}", inline=True)
        embed.add_field(name="Total Lost", value=f"${stats['total_lost']:,}", inline=True)
        embed.add_field(name="Net Profit/Loss", value=f"${net_profit:,}", inline=False)
        embed.add_field(name="Biggest Win", value=f"${stats['biggest_win']:,}", inline=True)
        embed.add_field(name="Games Played", value=stats['games_played'], inline=True)
        
        if stats['total_wagered'] > 0:
            win_rate = (stats['total_won'] / stats['total_wagered']) * 100
            embed.add_field(name="Return Rate", value=f"{win_rate:.2f}%", inline=True)

        await ctx.send(embed=embed)


    @has_account()
    @commands.command(name="housestats")
    @commands.has_permissions(administrator=True)
    async def house_stats(self, ctx):
        total_wagered = sum(user["total_wagered"] for user in self.stats.values())
        total_won = sum(user["total_won"] for user in self.stats.values())
        total_lost = sum(user["total_lost"] for user in self.stats.values())
        total_games = sum(user["games_played"] for user in self.stats.values())
        
        house_profit = total_lost - total_won
        
        embed = discord.Embed(title="House Statistics", color=discord.Color.gold())
        embed.add_field(name="Total Wagered", value=f"${total_wagered:,}", inline=False)
        embed.add_field(name="House Profit", value=f"${house_profit:,}", inline=False)
        embed.add_field(name="Total Games Played", value=total_games, inline=False)
        
        if total_wagered > 0:
            house_edge = (house_profit / total_wagered) * 100
            embed.add_field(name="House Edge", value=f"{house_edge:.2f}%", inline=False)
        
        await ctx.send(embed=embed)        
# Add this method to your Economy class




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
                return str(self.bot.user.id), "House", True
            
            # Handle discord Member
            if isinstance(user, discord.Member):
                return str(user.id), user.name, True
            
            return None, None, False
        except Exception as e:
            print(f"Error in validate_user: {e}")
            return None, None, False
        
    def load_currency(self):
        try:
            with open('.json/currency.json', 'r') as f:
                self.currency = json.load(f)
        except FileNotFoundError:
            self.currency = {}

    def save_currency(self):
        with open('.json/currency.json', 'w') as f:
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

    def parse_amount(self, amount: str) -> int:
        """Parse amount with proper multiplier validation"""
        try:
            amount = amount.strip().lower()
            
            # Valid multipliers
            multipliers = {
                'k': 1_000,
                'm': 1_000_000,
                'b': 1_000_000_000,
                't': 1_000_000_000_000
            }

            # If amount ends with a letter
            if amount[-1].isalpha():
                multiplier = amount[-1]
                number = amount[:-1]

                # Check if it's a valid multiplier
                if multiplier not in multipliers:
                    raise ValueError("Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B, 1T)")

                try:
                    base_amount = float(number)
                    parsed_amount = int(base_amount * multipliers[multiplier])
                    
                    # Convert large B amounts to T if they exceed 1000B
                    if multiplier == 'b' and base_amount >= 1000:
                        parsed_amount = int((base_amount / 1000) * multipliers['t'])
                    
                    return parsed_amount
                except ValueError:
                    raise ValueError("Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B, 1T)")

            # If no multiplier, try to parse as regular number
            return int(float(amount))

        except ValueError as e:
            raise ValueError(str(e))
        except Exception:
            raise ValueError("Invalid amount! Use numbers with K, M, B, or T (e.g., 50M, 100M, 1B, 5B, 1T)")

    def format_amount(self, amount):
        # For amounts >= 100T
        if amount >= 100000000000000:  # 100T+
            trillions = amount / 1000000000000
            return f"{int(trillions)}T"
            
        # For amounts >= 10T
        elif amount >= 10000000000000:  # 10T+
            trillions = amount / 1000000000000
            return f"{trillions:.1f}T"
            
        # For amounts >= 1T
        elif amount >= 1000000000000:  # 1T+
            billions = amount / 1000000000
            return f"{int(billions):,}B"  # Added comma
            
        # For amounts >= 100B
        elif amount >= 100000000000:  # 100B+
            billions = amount / 1000000000
            return f"{int(billions)}B"
            
        # For amounts >= 10B
        elif amount >= 10000000000:  # 10B+
            billions = amount / 1000000000
            return f"{billions:.2f}B"
            
        # For amounts >= 1B
        elif amount >= 1000000000:  # 1B+
            millions = amount / 1000000
            return f"{int(millions):,}M"  # Added comma
            
        # For amounts >= 100M
        elif amount >= 100000000:  # 100M+
            millions = amount / 1000000
            return f"{int(millions)}M"
            
        # For amounts >= 10M
        elif amount >= 10000000:  # 10M+
            millions = amount / 1000000
            return f"{millions:.1f}M"
            
        # For amounts >= 1M
        elif amount >= 1000000:  # 1M+
            thousands = amount / 1000
            return f"{int(thousands):,}K"  # Added comma
            
        # For amounts >= 100K
        elif amount >= 100000:  # 100K+
            thousands = amount / 1000
            return f"{int(thousands)}K"
            
        # For amounts < 100K
        else:
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
        await asyncio.sleep(0.5)
        await ctx.message.delete()
        if not self.currency:
            await ctx.send("No balances found!")
            return

        # Filter out the house account and convert user IDs to int for sorting
        user_balances = []
        house_balance = 0
        total_money = 0  # Initialize total money counter
        
        for user_id, balance in self.currency.items():
            total_money += balance  # Add each balance to total
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
                title="Balance Rankings",
                description=page,
                color=discord.Color.gold()
            )
            # Add both page number and total money to footer
            embed.set_footer(text=f"Page {i}/{len(pages)} • Total Balance: {self.format_amount(total_money)}")
            embeds.append(embed)

        # Send the first embed with pagination
        view = PaginationView(embeds)
        message = await ctx.send(embed=embeds[0], view=view)
        view.message = message  # Store message reference for timeout handling
        
        # Wait 20 seconds then delete the message

    

    @commands.command(aliases=['bal'])
    @has_account()
    async def balance(self, ctx, *, user: typing.Optional[typing.Union[discord.Member, str]] = None):
        GP_TO_USD_RATE = 0.0000000196
        """Check your balance or someone else's balance"""
        try:
            # Check if user is specifically requesting house balance
            if isinstance(user, str) and user.lower() == 'house':
                house_balance = await self.get_balance('house')
                house_usd = house_balance * GP_TO_USD_RATE
                
                embed = discord.Embed(
                    title="🏦 House Balance",
                    description="",
                    color=discord.Color.purple()  # Using purple for house
                )
                
                embed.add_field(
                    name="Total House Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(house_balance)} GP",
                    inline=False
                )
                
                embed.set_footer(text=f"House Value - ${house_usd:.2f} USD")
                await ctx.send(embed=embed)
                return



            if user is None:
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
            USD = balance * GP_TO_USD_RATE
            
            # Get vault balance
            user_id = str(ctx.author.id)
            vault_data = self.load_vault_data()
            user_vault = vault_data.get(user_id, {"balance": 0})
            vault_balance = user_vault.get("balance", 0)
            print(f"Current vault balance: ${vault_balance:,}")
            vaultplusbalance = vault_balance + balance
            VAULT_USD = vault_balance * GP_TO_USD_RATE
            total_usd = vaultplusbalance * GP_TO_USD_RATE




            if balance == 0 and vault_balance == 0:
                embed = discord.Embed(
                    title="Empty Balance!",
                    description=f"You have no gp!\nUse `,deposit <amount> <rsn>` to get started!",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"🏦 {ctx.author.display_name.title()}'s Balance",
                    color=discord.Color.gold()
                )
                
                # Wallet balance (left side)
                embed.add_field(
                    name="Wallet Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(balance)} GP",
                    inline=True
                )
                
                # Vault balance (right side)
                embed.add_field( 
                    name="Vault Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(vault_balance)} GP",
                    inline=True,
                )

                embed.add_field(
                    name=" ",
                    value=f"`,withdraw or ,deposit <gp> <rsn>`\n`,staking to see more commands.`",
                    inline=False
                )                
                # Add the commands as description
                embed.set_footer(text=f"Total balance {self.format_amount(vaultplusbalance)} GP / ${total_usd:.2f} USD", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")






    @commands.command(aliases=['give'])
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
                    await ctx.send("Invalid user! Example : ,add @user 100 or ,add house 1000")
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
                await ctx.send("Invalid amount format! Use numbers with K, M, or B (e.g., 1.5K, 2M, 3B, 1T)")
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
                final_balance = self.currency[user_id]
                
                # Save changes
                self.save_currency()
                target_ctx = copy.copy(ctx)
                target_ctx.author = user  # Set the author to the target user
                
                # Log the transaction for the target user
                if (isinstance(user, discord.Member) and user.id == self.bot.user.id) or (isinstance(user, str) and user.lower() == "house"):

                    # This is a house transaction (bot ID was targeted)
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=amount,
                        final_balance=final_balance,
                        transaction_type="add",
                        is_house=True
                    )
                else:
                    # This is a regular user transaction
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=amount,
                        final_balance=final_balance,
                        transaction_type="add"
                    )
                # Add this after the transaction is completed but before the final confirmation message
                if isinstance(user, discord.Member):  # Only send DM if it's a Discord member (not house)
                    try:
                        dm_embed = discord.Embed(
                            title="Your deposit has been completed!",
                            description=f"An admin has added currency to your balance.",
                            color=discord.Color.green()
                        )
                        dm_embed.add_field(
                            name="Amount Added",
                            value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}",
                            inline=False
                        )
                        dm_embed.add_field(
                            name="New Balance",
                            value=f"<:goldpoints:1319902464115343473> {self.format_amount(final_balance)}",
                            inline=False
                        )
                        dm_embed.add_field(
                            name="Added By",
                            value=f"{ctx.author.mention}",
                            inline=False
                        )
                        dm_embed.set_footer(text=f"Transaction ID: {ctx.message.id}")
                        
                        await user.send(embed=dm_embed)
                    except discord.Forbidden:
                        # If user has DMs closed
                        await ctx.send(f"Note: Couldn't send DM to {user.name} (DMs might be closed)")
                    except Exception as e:
                        # Handle any other potential errors
                        await ctx.send(f"Note: Couldn't send DM to {user.name} ({str(e)})")
              
                
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
                    await ctx.send("Invalid user! Example ,remove @user 1000 or ,remove house 1000")
                    return

            # Validate user
            user_id, user_name, valid = await self.validate_user(user)
            if not valid:
                await ctx.send("Invalid user! Example ,remove @user 1000 or ,remove house 1000")
                return

            # Parse amount
            try:
                amount = self.parse_amount(amount)
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, or B (e.g., 1.5K, 2M, 3B, 1T)")
                return

            if amount <= 0:
                await ctx.send("Amount must be positive!")
                return

            # Check if user has enough balance
            current_balance = await self.get_balance(user_id)
            if current_balance < amount:
                await ctx.send(f"{user_name} doesn't have enough balance! Their balance: <:goldpoints:1319902464115343473> {self.format_amount(current_balance)}")
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
                final_balance = self.currency[user_id]
                
                # Save changes
                self.save_currency()
                target_ctx = copy.copy(ctx)
                target_ctx.author = user  # Set the author to the target user
                
                # Log the transaction for the target user
                if (isinstance(user, discord.Member) and user.id == self.bot.user.id) or (isinstance(user, str) and user.lower() == "house"):

                    # This is a house transaction (bot ID was targeted)
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=amount,
                        final_balance=final_balance,
                        transaction_type="remove",
                        is_house=True
                    )
                else:
                    # This is a regular user transaction
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=amount,
                        final_balance=final_balance,
                        transaction_type="remove"
                    )            
                

                if isinstance(user, discord.Member):  # Only send DM if it's a Discord member (not house)
                    try:
                        dm_embed = discord.Embed(
                            title="Your withdrawal has been completed!",
                            description=f"An admin has removed currency from your balance.",
                            color=discord.Color.red()
                        )
                        dm_embed.add_field(
                            name="Amount Withdrawn",
                            value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}",
                            inline=False
                        )
                        dm_embed.add_field(
                            name="New Balance",
                            value=f"<:goldpoints:1319902464115343473> {self.format_amount(final_balance)}",
                            inline=False
                        )
                        dm_embed.add_field(
                            name="Removed By",
                            value=f"{ctx.author.mention}",
                            inline=False
                        )
                        dm_embed.set_footer(text=f"Transaction ID: {ctx.message.id}")
                        
                        await user.send(embed=dm_embed)
                    except discord.Forbidden:
                        # If user has DMs closed
                        await ctx.send(f"Note: Couldn't send DM to {user.name} (DMs might be closed)")
                    except Exception as e:
                        # Handle any other potential errors
                        await ctx.send(f"Note: Couldn't send DM to {user.name} ({str(e)})")


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

    @has_account()
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
                    await ctx.send("Invalid recipient! ,transfer <user> <amount>")
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
                await ctx.send("Invalid amount format! Use numbers with K, M, or B (e.g., 1.5K, 2M, 3B, 1T)")
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
                await ctx.send(f"You don't have enough balance!\n Your balance: <:goldpoints:1319902464115343473> {self.format_amount(sender_balance)}\n\n Use ,deposit <amount> <rsn> to add more.")
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
                
                # Get new balances
                sender_final_balance = await self.get_balance(sender_id)
                recipient_final_balance = await self.get_balance(recipient_id)
                
                # Log transaction for sender
                await self.log_transaction(
                    ctx=ctx,
                    bet_amount=0,
                    win_amount=-amount,  # Negative because they're sending
                    final_balance=sender_final_balance,
                    transaction_type="transfer",
                    is_house=False
                )
                
                # Log transaction for recipient (if not house)
                if recipient_arg.lower() == "house":
                    # Log house transaction
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=-amount,  # Negative because they're sending
                        final_balance=sender_final_balance,
                        transaction_type="transfer",
                        is_house=True
                    )
                else:
                    # Create recipient context and log regular transfer
                    recipient_ctx = copy.copy(ctx)
                    recipient_ctx.author = recipient
                    await self.log_transaction(
                        ctx=ctx,
                        bet_amount=0,
                        win_amount=-amount,  # Negative because they're sending
                        final_balance=sender_final_balance,
                        transaction_type="transfer",
                        is_house=False
                    )
                
                embed = discord.Embed(
                    title="Transfer Successful!",
                    description=f"Transferred <:goldpoints:1319902464115343473> {self.format_amount(amount)} to {recipient_name}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Your New Balance",
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(sender_final_balance)}"
                )
                
                await confirm_msg.edit(content=None, embed=embed, view=None)
            else:
                await confirm_msg.edit(content="Transfer cancelled.", view=None)
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    
    @commands.command(name='cleartransactions', aliases=['cleartrans'])
    @commands.is_owner()
    async def clear_transactions(self, ctx, target: typing.Optional[discord.Member] = None, option: str = None):
        """Clear transaction logs for a user or all users"""
        
        try:
            with open('logs/transactions.json', 'r') as f:
                logs = json.load(f)
        except FileNotFoundError:
            return await ctx.send("No transaction logs found.")

        if not logs.get("users"):
            return await ctx.send("No transactions to clear.")

        # If "all" option is specified, ask for confirmation
        if option and option.lower() == 'all':
            confirm_msg = await ctx.send("⚠️ Are you sure you want to clear ALL transaction logs for ALL users? This cannot be undone!\n"
                                    "React with ✅ to confirm or ❌ to cancel.")
            await confirm_msg.add_reaction('✅')
            await confirm_msg.add_reaction('❌')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message == confirm_msg

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == '✅':
                    # Clear all transactions but keep the structure
                    logs["users"] = {}
                    with open('logs/transactions.json', 'w') as f:
                        json.dump(logs, f, indent=2)
                    await ctx.send("✅ Cleared all transaction logs for all users.")
                else:
                    await ctx.send("<:remove:1328511957208268800>  Operation cancelled.")
                return
                
            except asyncio.TimeoutError:
                await ctx.send("<:remove:1328511957208268800> Confirmation timed out. Operation cancelled.")
                return

        # If no target specified, default to command user
        if not target:
            target = ctx.author

        user_id = str(target.id)
        
        if user_id not in logs["users"]:
            return await ctx.send(f"No transactions found for {target.display_name}.")

        # Ask for confirmation for individual user clear
        confirm_msg = await ctx.send(f"⚠️ Are you sure you want to clear all transaction logs for {target.display_name}?\n"
                                "React with ✅ to confirm or ❌ to cancel.")
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message == confirm_msg

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                # Remove user's transactions
                del logs["users"][user_id]
                with open('logs/transactions.json', 'w') as f:
                    json.dump(logs, f, indent=2)
                await ctx.send(f"✅ Cleared all transaction logs for {target.display_name}.")
            else:
                await ctx.send("❌ Operation cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("❌ Confirmation timed out. Operation cancelled.")



    @has_account()
    @commands.command()
    async def staking(self, ctx):
        await ctx.message.delete()

        # Get commands from multiple cogs
        commands_list = []
        cogs_to_include = ['Economy', 'GambleSystem', 'LevelSystem', 'Profile']  # Add the names of cogs you want to include
        
        for cog_name in cogs_to_include:
            cog = self.bot.get_cog(cog_name)
            if cog:
                commands_list.extend(cog.get_commands())
        
        # Sort all commands alphabetically
        commands_list = sorted(commands_list, key=lambda x: x.name)

        # Rest of your existing code remains the same
        command_descriptions = []
        for cmd in commands_list:
            aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            description = cmd.help or "No description available"
            command_descriptions.append(f"`,{cmd.name}{aliases}`")

        # Split into pages (5 commands per page)
        pages = []
        page_size = 7
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
            embed.set_footer(text=f"Page {i}/{len(pages)} • Command list will be deleted after 30s of inactivity", icon_url=ctx.author.avatar.url)
            embeds.append(embed)

        # Send message with pagination
        view = PaginationView(embeds)
        message = await ctx.send(embed=embeds[0], view=view)
        view.message = message
        


    @has_account()
    @commands.command(name="pvpflip", aliases=["flip", "challenge", "cf"])
    @transaction_limit()
    @user_lock()
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
                await ctx.send("Invalid bet amount! Use numbers with K, M, or B (e.g., 1.5K, 2M, 3B, 1T)")
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
            house_id = "1233966655923552370"

            # Verify both players have enough balance
            if challenger_balance < bet_amount:
                await ctx.send(f"You don't have enough balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(challenger_balance)}\n\n Use ,deposit <amount> <rsn> to add more.")
                return

            if opponent_balance < bet_amount:
                await ctx.send(f"{opponent.name} doesn't have enough balance! Their balance: <:goldpoints:1319902464115343473> {self.format_amount(opponent_balance)}")
                return

            house_tax = int(bet_amount * 0.05)  # 5% house tax
            win_amount = bet_amount * 2 - house_tax

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

            # Create contexts for both players
            winner_ctx = copy.copy(ctx)
            winner_ctx.author = winner
            
            loser_ctx = copy.copy(ctx)
            loser_ctx.author = loser

            # Log transaction for winner
            await self.log_transaction(
                ctx=winner_ctx,
                bet_amount=bet_amount,
                win_amount=win_amount,  # They win the bet minus house tax
                final_balance=self.currency[winner_id],
                transaction_type="game",
                is_house=False
            )

            # Log transaction for loser
            await self.log_transaction(
                ctx=loser_ctx,
                bet_amount=bet_amount,
                win_amount=-bet_amount,  # They lose their bet
                final_balance=self.currency[loser_id],
                transaction_type="game",
                is_house=False
            )

            self.update_stats(winner_id, bet_amount, win_amount)  # Winner gets win_amount as profit
            self.update_stats(loser_id, bet_amount, 0)  # Loser gets 0 winnings

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


    async def spin_animation(self, embed, msg, final_symbols, weighted_symbols):
        for position in range(3):
            # Random number of spins for each position (3-5)
            spins = random.randint(3, 5)
            used_symbols = set()  # Track used symbols to avoid repetition
            
            for _ in range(spins):
                temp_symbols = list(final_symbols)
                
                # Generate a new random symbol that hasn't been used yet
                available_symbols = [s for s in weighted_symbols if s not in used_symbols]
                if not available_symbols:  # Reset if we run out of unique symbols
                    used_symbols.clear()
                    available_symbols = weighted_symbols
                    
                random_symbol = random.choice(available_symbols)
                used_symbols.add(random_symbol)
                
                # Update the current position with the new symbol
                temp_symbols[position] = random_symbol
                
                # For positions not yet reached, show random spinning symbols
                for i in range(position + 1, 3):
                    temp_symbols[i] = random.choice(weighted_symbols)
                    
                embed.set_field_at(0, name="Spinning...", 
                                value=f"| {' | '.join(temp_symbols)} |")
                await msg.edit(embed=embed)
                await asyncio.sleep(0.5)
            
            # After spins complete, show the actual final symbol for this position
            temp_symbols = list(final_symbols[:position + 1])
            for i in range(position + 1, 3):
                temp_symbols.append(random.choice(weighted_symbols))
                
            embed.set_field_at(0, name="Results" if position == 2 else "Spinning...", 
                            value=f"| {' | '.join(temp_symbols)} |")
            await msg.edit(embed=embed)
            await asyncio.sleep(0.5)

    def generate_symbols(self, guaranteed_match=False):
        symbol_list = list(self.symbols.keys())
        weights = [data["weight"] for data in self.symbols.values()]
        
        if guaranteed_match:
            # Pick a random symbol for the match
            match_symbol = random.choices(symbol_list, weights=weights, k=1)[0]
            
            # For three matching symbols (3% chance)
            if random.random() < 0.07:
                return [match_symbol] * 3
                
            # For two matching symbols (7% chance)
            elif random.random() < 0.14:
                result = [match_symbol] * 2
                # Add one different symbol
                remaining_symbols = [s for s in symbol_list if s != match_symbol]
                remaining_weights = [weights[symbol_list.index(s)] for s in remaining_symbols]
                result.append(random.choices(remaining_symbols, weights=remaining_weights, k=1)[0])
                random.shuffle(result)  # Randomize position of matches
                return result

        # No guaranteed matches - generate each reel independently
        result = []
        for _ in range(3):
            symbol = random.choices(symbol_list, weights=weights, k=1)[0]
            result.append(symbol)
        
        return result


    @has_account()
    @commands.command(name="slots", aliases=["gamble", "slot"])
    @confirm_bet()
    @transaction_limit()
    @user_lock()
    async def slots(self, ctx, amount=None):
        # Define slot machine symbols with weights and multipliers (total weight = 100)
        symbols = self.symbols
        
        # Create weighted symbol list
        weighted_symbols = []
        for symbol, data in symbols.items():
            weighted_symbols.extend([symbol] * data["weight"])

        if amount is None:
                    # Help embed code
                    help_embed = discord.Embed(
                        title="<:gamba:1328512027282374718> Slot Machine Guide <:gamba:1328512027282374718>",
                        description="Bet your coins for a chance to win big!\nUse: `,slots <amount>`",
                        color=discord.Color.gold()
                    )
                    # Add symbol information
                    symbols_info = ""
                    for symbol, data in self.symbols.items():
                        multiplier = data["multiplier"]
                        chance = data["weight"]
                        symbols_info += f"{symbol} **{data['name']}** - {multiplier}x multiplier\n"

                    help_embed.add_field(
                        name="Symbols & Multipliers",
                        value=symbols_info,
                        inline=False
                    )
                    help_embed.add_field(
                        name="Winning Combinations",
                        value=(
                            "**Three of a kind:** Full multiplier payout\n"
                            "**Two of a kind:** 40% of symbol multiplier\n"
                            "**No matches:** Loss of bet\n"
                            "\n*Note: A 5% tax is applied to all winnings*"
                        ),
                        inline=False
                    )
                    help_embed.add_field(
                        name="Example",
                        value=",gamble 5M - Bets 5,000,000 coins",
                        inline=False
                    )
                    await ctx.send(embed=help_embed)
                    return

        try:
            # Get user and house info
            user_id = str(ctx.author.id)
            house_id = str(self.bot.user.id)
            print(f"User ID: {user_id}, House ID: {house_id}")
        
            user_balance = await self.get_balance(user_id)

            
            if house_id not in self.currency:
                self.currency[house_id] = 0   

            # Validate bet and balances
            if amount <= 0:
                await ctx.send("You must bet at least 1 coin!")
                return
                        
            if amount > user_balance:
                await ctx.send(f"You don't have enough coins! Your balance: {self.format_amount(user_balance)} <:goldpoints:1319902464115343473> ")
                return

            # Check house balance
            house_balance = int(self.currency[house_id])
            max_possible_win = amount * 30  # Maximum possible win (Diamond 30x)
            if house_balance < max_possible_win:
                await ctx.send("The house doesn't have enough balance to cover potential winnings! Please try a smaller bet.")
                return

            # Deduct bet ONCE at the start
            self.currency[user_id] -= amount
            self.currency[house_id] += amount
            while_betting_balance = await self.get_balance(user_id)

            # Create and send initial embed
            embed = discord.Embed(title="<:gamba:1328512027282374718> Slot Machine <:gamba:1328512027282374718>", color=discord.Color.gold())
            embed.add_field(name="Spinning...", value="| ❓ | ❓ | ❓ |")
            embed.set_footer(text=f"Balance: {self.format_amount(while_betting_balance)} GP", icon_url=ctx.author.avatar.url)
            msg = await ctx.send(embed=embed)

            # Generate final results
            guaranteed_match = random.random() < 0.1  # 10% chance for a guaranteed match
            final_symbols = self.generate_symbols(guaranteed_match=guaranteed_match)

            # Spinning animation
            await self.spin_animation(embed, msg, final_symbols, weighted_symbols)

            # Calculate matches
            symbol_counts = {}
            for symbol in final_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            max_matches = max(symbol_counts.values())

            # Calculate and apply winnings
            if max_matches == 3:
                symbol = max(symbol_counts, key=symbol_counts.get)
                multiplier = symbols[symbol]["multiplier"]
                gross_win = amount * multiplier
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                
                # Add winnings (bet already deducted)
                self.currency[user_id] += winnings
                self.currency[house_id] -= winnings
                
                # Get final balance after transaction
                final_balance = int(self.currency[user_id])
                
                result = f"🎉 JACKPOT! Triple {symbols[symbol]['name']}! 🎉"
                await self.log_transaction(ctx, amount, winnings, final_balance, is_house=False)
                
            elif max_matches == 2:
                matching_symbol = [s for s, count in symbol_counts.items() if count == 2][0]
                base_multiplier = symbols[matching_symbol]["multiplier"]
                multiplier = base_multiplier * 0.4
                gross_win = int(amount * multiplier)
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                
                # Add winnings (bet already deducted)
                self.currency[user_id] += winnings
                self.currency[house_id] -= winnings
                
                # Get final balance after transaction
                final_balance = int(self.currency[user_id])
                
                result = f"🎈 Double {symbols[matching_symbol]['name']}! 🎈"
                await self.log_transaction(ctx, amount, winnings, final_balance, is_house=False)
                
            else:
                winnings = 0
                # Get final balance after bet was deducted
                final_balance = int(self.currency[user_id])
                tax_amount = 0
                result = "No match!"
                await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)

            # Update stats and save
            self.update_stats(user_id, amount, winnings)
            self.save_currency()

            # Create result embed
            result_embed = discord.Embed(
                title="<:gamba:1328512027282374718> Slot Machine Results <:gamba:1328512027282374718>",
                color=discord.Color.green() if winnings > 0 else discord.Color.red()
            )
            
            result_embed.add_field(
                name=result,
                value=f"| {' | '.join(final_symbols)} |",
                inline=False
            )
            
            result_embed.add_field(
                name="Outcome",
                value=f"Bet: {self.format_amount(amount)}\n"
                    f"Win: +{self.format_amount(winnings)}\n"
                    f"Tax: {self.format_amount(tax_amount)}",
                inline=False
            )
            
            result_embed.set_footer(
                text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} GP", icon_url=ctx.author.avatar.url
            )

            await msg.edit(embed=result_embed)

        except Exception as e:
            print(f"Error in slots: {str(e)}")
            await ctx.send("<:remove:1328511957208268800> An error occurred while processing your bet.")



    @has_account()
    @commands.command(aliases=["stake", "flowers"])
    @confirm_bet()
    @transaction_limit()
    @user_lock()
    async def flower(self, ctx, bet_amount: typing.Optional[str] = None):

        user_id = ctx.author.id
    
        
        if bet_amount is None:
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
                    "• Use `,flower <bet amount> player` to play as Player!\n"
                    "• Use `,flower <bet amount> banker` to play as Banker!\n"
                    "• Get a higher total than the opponent to win!\n"
                    "• Numbers over 10 reset (eg: 12 becomes 2)"
                ),
                inline=False
            )
            
            await ctx.send(embed=help_embed)
            return

        # If bet_amount is provided, continue with the existing game logic
        try:
            print(f"Raw bet_amount: {bet_amount!r}")
            
            # Make sure bet_amount is a string and strip any whitespace
            bet_amount = str(bet_amount).strip()
            print(f"Processed bet_amount: {bet_amount!r}")
            
            # Try to parse the amount
            amount = self.parse_amount(bet_amount)
            print(f"Parsed amount: {amount}")

                     
            # Flowers with their values and weights (odds)
            flowers = {
                "<:rainbow:1326018658648195103>": {"value": 0, "weight": 12},    
                "<:pastel:1326018646098706564>": {"value": 0, "weight": 12},    
                "<:red:1326018733826773023>": {"value": 2, "weight": 15},    
                "<:blue:1326018721730396190>": {"value": 5, "weight": 15},    
                "<:yellow:1326018708136792085>": {"value": 4, "weight": 15},   
                "<:purple:1326018686817009734>": {"value": 3, "weight": 15},    
                "<:orange:1326018671763521557>": {"value": 6, "weight": 15},    
                "<:white:1326018610719756340>": {"value": 69, "weight": 0.1},  
                "<:black:1326018632739721327>": {"value": 420, "weight": 0.2}  
            }

            # Validate bet amount first

            if amount <= 0:
                await ctx.send("Please enter a valid bet amount!")
                return
            house_id = str(self.bot.user.id)
            print(f"House ID {house_id}")


                        # Create buttons for side selection
            class SideButtons(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=30)
                    self.value = None

                @discord.ui.button(label="Player", style=discord.ButtonStyle.green)
                async def player(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == ctx.author.id:
                        self.value = "player"
                        self.stop()
                        await interaction.message.delete()  # Delete the message with buttons

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == ctx.author.id:
                        self.stop()
                        await interaction.message.delete()  # Delete the message with buttons  

                @discord.ui.button(label="Banker", style=discord.ButtonStyle.blurple)
                async def banker(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id == ctx.author.id:
                        self.value = "banker"
                        self.stop()
                        await interaction.message.delete()  # Delete the message with buttons
                        
                      

            # Show side selection buttons
            view = SideButtons()
            embed = discord.Embed(
                title="Choose Your Side",
                description="Click a button to choose your side:",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Bet Amount", 
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(amount)}", 
                inline=False
            )

            selection_message = await ctx.send(embed=embed, view=view)

            # Wait for button press
            await view.wait()

            # If no button was pressed (timeout)
            if view.value is None:
                await selection_message.delete()
                await ctx.send("Game cancelled - no side selected in time!")
                return
                
            side = view.value  # This will be either "player" or "banker"            
            if house_id not in self.currency:
                self.currency[house_id] = 0      
  


            max_possible_win = amount  
            if int(self.currency[house_id]) < max_possible_win:
                print(f"House balance: {self.currency[house_id]}")
                print(f"amount: {amount}")
                print(f"Max possible win: {max_possible_win}")
                await ctx.send("The house doesn't have enough balance to cover potential winnings! Please try a smaller bet.")
                return             

            # Check if user has enough balance
            user_id = str(ctx.author.id)
            if user_id not in self.currency:
                self.currency[user_id] = 0

           # If they dont, tell them they dont have enough balance
            
            if self.currency[user_id] < amount:
                await ctx.send(f"You don't have enough balance for this bet! Your balance: {self.format_amount(await self.get_balance(user_id))} <:goldpoints:1319902464115343473>\n\n Use ,deposit <amount> <rsn> to add more.")
                return

            print(f"taking {amount} from {user_id} for flower game")
            self.currency[user_id] -= amount
            print(f"giving {amount} to house")
            self.currency[house_id] += amount 
            self.save_currency()  

  

  

            def calculate_total(numbers):
                """Calculate total, implementing the 10+ reset rule after the sum."""
                print(f"Received numbers to calculate: {numbers}")  
                total = sum(numbers) 
                final_total = sum(numbers) % 10                
                print(f"Running total (before mod 10): {total}")  
                print(f"Final total: {final_total}")  
                return total % 10   


            def needs_third_card(total):
                """Determine if a third card is needed (5 or below)"""
                print(f"Checking if third card is needed for total: {total}")
                return total <= 5
                

            def pick_flower():
                """Pick a random flower based on weights"""
                flower_list = list(flowers.keys())
                weights = [flowers[f]["weight"] for f in flower_list]
                chosen_flower = random.choices(flower_list, weights=weights, k=1)[0]
                print(f"Picked flower: {chosen_flower} with value: {flowers[chosen_flower]['value']}")
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
                value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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
                player_hand.append(p_value)
                player_flowers[i] = p_flower

                # Clear previous fields and update the embed
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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

                def check_special_flowers(hand_values, flowers_display):
                    for value, flower in zip(hand_values, flowers_display):
                        if value == 69:  # White Flower
                            return "win", f"**WHITE FLOWER!** Instant Win! 💰\n", discord.Color.green()
                        elif value == 420:  # Black Flower
                            return "loss", "**BLACK FLOWER!** House Wins! 💀", discord.Color.red()
                    return None, None, None

                # Check player's hand for special flowers
                result, message, color = check_special_flowers(player_hand, player_flowers)
                if result:
                    game_embed.color = color
                    game_embed.add_field(
                        name="Result", 
                        value=message, 
                        inline=False
                    )
                    await game_message.edit(embed=game_embed)
                    
                    if result == "win":
                        winnings = amount * 2
                        tax_amount = int(winnings * 0.05)
                        net_winnings = winnings - tax_amount
                        print(f"Player wins {winnings} GP, tax: {tax_amount}, net: {net_winnings} from a white flower!")
                        self.currency[house_id] -= winnings
                        self.currency[user_id] += net_winnings
                        self.currency[house_id] += tax_amount
                        self.update_stats(user_id, amount, net_winnings)
                        final_balance = await self.get_balance(user_id)
                        print(f"+{winnings} %{tax_amount} net +{net_winnings} ${final_balance}")


                    else:
                        self.update_stats(user_id, amount, amount)
                        final_balance = await self.get_balance(user_id)
            
                        await self.log_transaction(ctx, amount, 0, final_balance, is_house=False)
                        print(f"-{amount} ${final_balance} THIS IS A BLACK FLOWER")
                    
                    self.save_currency()
                    return
                

                

                
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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


            # Check if the player needs a third card
            player_total = calculate_total(player_hand)
            if needs_third_card(player_total):
                game_embed.add_field(
                    name="Status", 
                    value="Drawing third card for player...", 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                await asyncio.sleep(1)

                # Pick a new flower and value for the third card
                p_flower, p_value = pick_flower()  # New card for third draw
                player_hand.append(p_value)
                player_flowers[2] = p_flower
                player_total = sum(player_hand) % 10 
                print(f"Player's hand after third card: {player_hand}")
                print(f"Final total after third card: {player_total}")  # Assign the third card properly

                # Update the embed with the new hand
                game_embed.clear_fields()
                game_embed.add_field(
                    name="Your Bet", 
                    value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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
                    value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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
                print(f"Banker's total: {banker_total}, needs third card")
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
                    value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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

            result, message, color = check_special_flowers(banker_hand, banker_flowers)
            if result:
                game_embed.color = color
                game_embed.add_field(
                    name="Result", 
                    value=message, 
                    inline=False
                )
                await game_message.edit(embed=game_embed)
                
                if result == "win":
                    self.currency[user_id] += amount
                    winnings = amount * 1.95
                    self.update_stats(user_id, amount, winnings)
                else:
                    self.currency[user_id] += amount  # Player wins
                
                self.save_currency()
                return

            # Final result embed
            final_embed = discord.Embed(title="<:seeds:1326024477145956433> Flower Staking Game", color=discord.Color.gold())
            final_embed.add_field(
                name="Your Bet", 
                value=f"<:goldpoints:1319902464115343473> __**{self.format_amount(amount)}**__ on __**{side.title()}**__", 
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
               
            # Determine winner and update balances

            if player_total == 9 and banker_total == 9:
                # Tie on 9s, banker wins
                if side == "banker":
                    final_embed.add_field(
                        name="Result", 
                        value="Double 9s! Banker wins! <a:xdd:1221066292631568456>", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )
                    self.update_stats(user_id, amount, 0)
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)
                    
                else:
                    # Player bet on player and lost
                    final_embed.add_field(
                        name="Result", 
                        value="Double 9s! Banker wins! <a:xdd:1221066292631568456>", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )
                    self.update_stats(user_id, amount, 0)
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)

            elif player_total > banker_total:
                if side == "player":
                    # Player bet on player and won
                    winnings = amount * 2
                    tax_amount = int(winnings * 0.05)
                    net_winnings = winnings - tax_amount
                    self.currency[user_id] += net_winnings
                    self.currency[house_id] -= winnings
                    self.currency[house_id] += tax_amount
                    self.update_stats(user_id, amount, net_winnings)
                    
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, net_winnings, final_balance, is_house=False)
                    
                    final_embed.add_field(
                        name="Result", 
                        value=f"Player wins! You win! <a:MUGA:1178140574570790954>\nWinnings: {self.format_amount(net_winnings)} (After 5% tax)", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )                    
                else:
                    # Player bet on banker and lost
                    final_embed.add_field(
                        name="Result", 
                        value="Player wins! You lose! <a:xdd:1221066292631568456>", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )
                    self.update_stats(user_id, amount, 0)
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)

            elif banker_total > player_total:
                if side == "banker":
                    # Player bet on banker and won
                    winnings = amount * 2  # Slightly lower multiplier for banker
                    tax_amount = int(winnings * 0.05)
                    net_winnings = winnings - tax_amount
                    self.currency[user_id] += net_winnings
                    self.currency[house_id] -= winnings
                    self.currency[house_id] += tax_amount
                    self.update_stats(user_id, amount, net_winnings)
                    
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, net_winnings, final_balance, is_house=False)
                    
                    final_embed.add_field(
                        name="Result", 
                        value=f"Banker wins! You win! <a:MUGA:1178140574570790954>\nWinnings: {self.format_amount(net_winnings)} (After 5% tax)", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )                    
                else:
                    # Player bet on player and lost
                    final_embed.add_field(
                        name="Result", 
                        value="Banker wins! You lose! <a:xdd:1221066292631568456>", 
                        inline=False
                    )
                    final_embed.set_footer(
                        text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} ", icon_url=ctx.author.avatar.url
                    )
                    self.update_stats(user_id, amount, 0)
                    final_balance = await self.get_balance(user_id)
                    await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)

            else:
                # Tie (push)
                self.currency[user_id] += amount  # Refund the bet
                self.currency[house_id] -= amount
                final_balance = await self.get_balance(user_id)
                await self.log_transaction(ctx, amount, 0, final_balance, is_house=False)
                self.update_stats(user_id, amount, amount)
                final_embed.add_field(
                    name="Result", 
                    value="Tie! It's a push. <a:aware:1255561720810831912>", 
                    inline=False
                )

                final_embed.set_footer(
                    text=f"Balance is the same: {self.format_amount(await self.get_balance(user_id))} <:goldpoints:1319902464115343473>", icon_url=ctx.author.avatar.url
                )


            # Save the updated currency values


            self.save_currency()
            await game_message.edit(embed=final_embed)

        except Exception as e:
            # Refund the bet amount in case of an error
            print(f"An error occurred: {str(e)}, refunding bet: {amount}")
            self.currency[user_id] += amount
            self.currency[house_id] -= amount
            self.save_currency()
            await ctx.send(f"An error occurred: {str(e)}. Your bet has been refunded.")
            return







    @commands.command(name="limits")
    @commands.is_owner()  # Only admins can change limits
    async def set_limits(self, ctx, min_amount: str = None, max_amount: str = None):
        """Set minimum and maximum gambling limits"""
        
        # If no arguments, show current limits
        if min_amount is None or max_amount is None:
            embed = discord.Embed(title="Current Gambling Limits", color=discord.Color.gold())
            embed.add_field(name="Minimum Bet", value=f"${limits_manager.current_min:,}", inline=False)
            embed.add_field(name="Maximum Bet", value=f"${limits_manager.current_max:,}", inline=False)
            await ctx.send(embed=embed)
            return

        # Parse amounts (supporting k, m, b notation)
        try:


            new_min = self.parse_amount(min_amount)
            new_max = self.parse_amount(max_amount)

            # Validation
            if new_min <= 0 or new_max <= 0:
                await ctx.send("<:remove:1328511957208268800> Limits must be positive numbers!")
                return

            if new_min >= new_max:
                await ctx.send("<:remove:1328511957208268800> Minimum limit must be less than maximum limit!")
                return

            # Update limits
            limits_manager.current_min = new_min
            limits_manager.current_max = new_max
            limits_manager.save_limits()

            # Confirm changes
            embed = discord.Embed(title="Gambling Limits Updated", color=discord.Color.green())
            embed.add_field(name="New Minimum Bet", value=f"${new_min:,}", inline=False)
            embed.add_field(name="New Maximum Bet", value=f"${new_max:,}", inline=False)
            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("<:remove:1328511957208268800> Invalid amount format! Use numbers with optional k, m, or b suffix (e.g., 500k, 1m)")

    @set_limits.error
    async def limits_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("<:remove:1328511957208268800> You need administrator permissions to change limits!")



    @commands.command(name="setbalance", aliases=["setbal", "set"])
    @commands.is_owner() 
    async def set_balance(self, ctx, target: typing.Union[discord.Member, str], amount: str):
        """Set a user's balance or all users' balances to a specific amount"""
        try:
            # Parse the amount (supporting k, m, b notation)

            new_balance = self.parse_amount(amount)
            
            if isinstance(target, str) and target.lower() == "all":
                # Store old balances for the embed
                old_balances = self.currency.copy()
                
                # Update all balances
                for user_id in self.currency:
                    self.currency[user_id] = new_balance
                
                self.save_currency()

                # Create embed for response
                embed = discord.Embed(
                    title="All Balances Updated",
                    description=f"Set {len(self.currency)} user balances to {self.format_amount(new_balance)}",
                    color=discord.Color.green() if new_balance >= 0 else discord.Color.red()
                )
                embed.add_field(
                    name="Sample Changes",
                    value="\n".join([
                        f"<@{user_id}>: {self.format_amount(old_balances[user_id])} → {self.format_amount(new_balance)}"
                        for user_id in list(old_balances.keys())[:5]  # Show first 5 users as examples
                    ]) + ("\n..." if len(old_balances) > 5 else ""),
                    inline=False
                )

            else:
                # Original single-user logic
                user_id = str(target.id)
                old_balance = self.currency.get(user_id, 0)
                
                # Set the new balance
                self.currency[user_id] = new_balance
                self.save_currency()

                # Create embed for response
                embed = discord.Embed(
                    title="Balance Updated",
                    color=discord.Color.green() if new_balance >= 0 else discord.Color.red()
                )
                embed.add_field(
                    name="User", 
                    value=f"{target.mention}", 
                    inline=False
                )
                embed.add_field(
                    name="Old Balance", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(old_balance)}", 
                    inline=True
                )
                embed.add_field(
                    name="New Balance", 
                    value=f"<:goldpoints:1319902464115343473> {self.format_amount(new_balance)}", 
                    inline=True
                )

            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("<:remove:1328511957208268800> Invalid amount format! Use numbers with optional k, m, or b suffix (e.g., 500k, 1m)")
        except Exception as e:
            await ctx.send(f"<:remove:1328511957208268800> An error occurred: {str(e)}")

    @set_balance.error
    async def set_balance_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("<:remove:1328511957208268800> You need administrator permissions to set balances!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("<:remove:1328511957208268800> Usage: ,setbalance <@user|all> <amount>")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("<:remove:1328511957208268800> Could not find that user!")

    @has_account()
    @commands.group(invoke_without_command=True, aliases=["vaults"])
    async def vault(self, ctx):
        """Shows all vault commands"""
        embed = discord.Embed(
            title="🏦 Vault Commands",
            description="Secure storage for your currency",
            color=discord.Color.gold()
        )
        
        # Get all vault subcommands
        for command in self.vault.walk_commands():
            # Get command aliases if any
            aliases = f" ({', '.join(command.aliases)})" if command.aliases else ""
            
            # Get command description
            description = command.help or "No description available"
            
            # Format command syntax
            if command.signature:
                syntax = f",vault {command.name} {command.signature}"
            else:
                syntax = f",vault {command.name}"
                
            embed.add_field(
                name=f"{syntax}{aliases}",
                value=description,
                inline=False
            )

        embed.set_footer(text="Keep your wealth secure!", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)

        
    @has_account()
    def get_vault_balance(self, user_id):
        """Get vault balance with accumulated interest"""
        try:
            vault_data = self.load_vault_data()
            if user_id not in vault_data:
                return 0

            current_time = datetime.now().timestamp()
            last_interest = vault_data[user_id].get("last_interest", current_time)
            balance = vault_data[user_id]["balance"]

            # Calculate hours passed
            hours_passed = (current_time - last_interest) / 3600
            
            # Calculate interest (1% per day = 0.0417% per hour)
            hourly_rate = 0.0001042 #/ 24 hours
            interest = int(balance * hourly_rate * hours_passed)
            
            # Update balance and last interest time
            vault_data[user_id]["balance"] += interest
            vault_data[user_id]["last_interest"] = current_time
            self.save_vault_data(vault_data)
            
            return vault_data[user_id]["balance"]
            
        except Exception as e:
            print(f"Balance calculation error: {e}")
            return 0

    @has_account()
    @vault.command(name="balance", aliases=["bal"])
    async def vault_balance(self, ctx):
        """Check your vault balance"""
        try:
            user_id = str(ctx.author.id)
            vault_data = self.load_vault_data()
            
            user_vault = vault_data.get(user_id, {"balance": 0})
            vault_balance = user_vault.get("balance", 0)
            total_interest = int(vault_balance * 0.0025) 
            wallet_balance = self.currency.get(user_id, 0)
            total_worth = vault_balance + wallet_balance
            
            embed = discord.Embed(
                title="🏦 Personal Vault",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Stored Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(vault_balance)}",
                inline=False
            )
            
            embed.add_field(
                name="Interest Per day",
                value=f"<:goldpoints:1319902464115343473> +{self.format_amount(total_interest)} (0.25%)",
                inline=False
            )
            
            embed.add_field(
                name="Wallet Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(wallet_balance)}",
                inline=False
            )
            
            embed.add_field(
                name="Total Net Worth",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(total_worth)}",
                inline=False
            )

            if user_vault.get("locked", False):
                lock_until = datetime.fromtimestamp(user_vault.get("lock_until", 0))
                embed.add_field(
                    name="🔒 Vault Status",
                    value=f"Locked until {lock_until.strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )
            embed.set_footer(text=f"Use ',vault lock' to lock it and gain interest!", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Balance error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")



    @vault.command(name="deposit", aliases=["add"])
    @confirm_bet()
    async def vault_add(self, ctx, amount=None):
        """Deposit money into your vault"""
        try:
            if amount is None:
                await ctx.send("Please specify an amount to deposit!")
                return
                
            # Parse amount
            try:
                amount = self.parse_amount(str(amount))
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B)")
                return

            # Check minimum deposit
            if amount < 500000:
                await ctx.send("Minimum deposit amount is 500k!")
                return
                
            user_id = str(ctx.author.id)
            
            # Check if user has enough money
            if self.currency.get(user_id, 0) < amount:
                await ctx.send("You don't have enough money!")
                return
                
            # Load vault data
            vault_data = self.load_vault_data()
            
            # Initialize user's vault if it doesn't exist
            if user_id not in vault_data:
                vault_data[user_id] = {
                    "balance": amount,  # Set initial balance
                    "locked": False,
                    "lock_until": None
                }
            else:
                # Add to existing balance
                vault_data[user_id]["balance"] = vault_data[user_id]["balance"] + amount
                
            # Update wallet balance
            self.currency[user_id] -= amount
            
            # Save changes
            self.save_vault_data(vault_data)
            self.save_currency()
            
            embed = discord.Embed(
                title="🏦 Vault Deposit",
                description=f"Successfully deposited <:goldpoints:1319902464115343473> {self.format_amount(amount)}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="New Vault Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(vault_data[user_id]['balance'])}",
                inline=True
            )
            embed.add_field(
                name="New Wallet Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(self.currency[user_id])}",
                inline=True
            )
            
            final_balance = self.currency[user_id]  # Vault balance after deposit
            await self.log_transaction(
                ctx=ctx,
                bet_amount=0,
                win_amount=amount,  # Amount deposited
                final_balance=final_balance,
                transaction_type="vault_deposit"
            )            
            await ctx.send(embed=embed)
                
        except Exception as e:
            print(f"Deposit error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")
            # Refund if error occurs
            self.currency[user_id] += amount
            self.save_currency()

    @vault.command(name="withdraw", aliases=["remove"])
    async def vault_remove(self, ctx, amount=None):
        """Remove money from your vault"""
        try:
            if amount is None:
                await ctx.send("Please specify an amount to remove!")
                return
                
            # Parse amount
            try:
                amount = self.parse_amount(str(amount))
            except ValueError:
                await ctx.send("Invalid amount format! Use numbers with K, M, B, or T (e.g., 1.5K, 2M, 3B)")
                return
                
            user_id = str(ctx.author.id)
            vault_data = self.load_vault_data()
            
            # Check if user has a vault
            if user_id not in vault_data:
                await ctx.send("You don't have a vault yet!")
                return

            # Check if vault is locked
            if vault_data[user_id].get("locked", False):
                lock_time = datetime.fromtimestamp(vault_data[user_id]["lock_until"])
                if lock_time > datetime.now():
                    remaining = lock_time - datetime.now()
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    
                    embed = discord.Embed(
                        title="🔒 Vault Locked",
                        description=f"Your vault is currently locked!\nUnlocks in: {hours}h {minutes}m",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return
                else:
                    vault_data[user_id]["locked"] = False
                    vault_data[user_id]["lock_until"] = None
                    self.save_vault_data(vault_data)

            # Check balance
            if vault_data[user_id]["balance"] < amount:
                await ctx.send("You don't have enough in your vault!")
                return
                
            if amount < 500000:
                await ctx.send("Minimum withdrawal amount is 500k!")
                return

            # Update balances
            vault_data[user_id]["balance"] -= amount
            self.currency[user_id] = self.currency.get(user_id, 0) + amount
            
            # Save changes
            self.save_vault_data(vault_data)
            self.save_currency()
            
            embed = discord.Embed(
                title="🏦 Vault Withdrawal",
                description=f"Successfully withdrawn <:goldpoints:1319902464115343473> {self.format_amount(amount)}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="New Vault Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(vault_data[user_id]['balance'])}",
                inline=True
            )
            embed.add_field(
                name="New Wallet Balance",
                value=f"<:goldpoints:1319902464115343473> {self.format_amount(self.currency[user_id])}",
                inline=True
            )

            final_balance = self.currency[user_id]  # Wallet balance after withdrawal
            await self.log_transaction(
                ctx=ctx,
                bet_amount=0,
                win_amount=-amount,  # Negative amount for withdrawal
                final_balance=final_balance,
                transaction_type="vault_withdraw"
            )            
            await ctx.send(embed=embed)
                
        except Exception as e:
            print(f"Remove error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")


    @vault.command(name="leaderboard", aliases=["lb"])
    async def vault_leaderboard(self, ctx):
        """Display the vault leaderboard"""
        try:
            await ctx.message.delete()
            
            # Load vault data from JSON
            vault_data = self.load_vault_data()
            
            # Convert to list of (user_id, balance) tuples
            vault_list = [(user_id, data['balance']) for user_id, data in vault_data.items()]
            
            # Sort by balance (highest to lowest)
            vault_list.sort(key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title="🏦 Vault Leaderboard",
                description="Top Vault Holders",
                color=discord.Color.gold()
            )

            # Add top 10 players to embed
            for i, (user_id, balance) in enumerate(vault_list[:10], 1):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = user.name
                except:
                    username = f"User {user_id}"

                medal = ""
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = "👑"

                embed.add_field(
                    name=f"{medal} Rank #{i}",
                    value=f"**{username}**\n<:goldpoints:1319902464115343473> {self.format_amount(balance)}",
                    inline=False
                )

            # Add footer with total vaults
            total_vaults = len(vault_list)
            total_wealth = sum(balance for _, balance in vault_list)
            embed.set_footer(text=f"Total Vaults: {total_vaults} | Combined Wealth: {self.format_amount(total_wealth)}")

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"Leaderboard error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")


    def load_last_interest_time(self):
        try:
            # Check if the .json directory exists, if not create it
            if not os.path.exists('.json'):
                os.makedirs('.json')
                
            json_path = '.json/last_interest.json'
            
            # If file doesn't exist, create it with current time
            if not os.path.exists(json_path):
                current_time = datetime.now()
                with open(json_path, 'w') as f:
                    json.dump({'last_interest': current_time.timestamp()}, f)
                return current_time
                
            # If file exists, read from it
            with open(json_path, 'r') as f:
                data = json.load(f)
                return datetime.fromtimestamp(data['last_interest'])
                
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading last interest time: {e}")
            current_time = datetime.now()
            self.save_last_interest_time(current_time)
            return current_time

    def save_last_interest_time(self, timestamp):
        with open('.json/last_interest.json', 'w') as f:
            json.dump({'last_interest': timestamp.timestamp()}, f)

    async def process_interest_payment(self, payment_time):
        try:
            print(" ")
            print("=== Starting Interest Payment Process ===")
            print(f"Processing interest payment for {payment_time}")
            vault_data = self.load_vault_data()
            house_id = "1233966655923552370"  # Your house ID
            total_interest = 0
            
            print("\nChecking locked vaults...")
            locked_count = 0
            # First pass: Calculate total interest needed
            for user_id, data in vault_data.items():
                if data.get("locked", False):
                    locked_count += 1
                    current_balance = data.get("balance", 0)
                    interest = int(current_balance * 0.0025)
                    total_interest += interest
                    print(f"User {user_id}: Balance={current_balance}, Interest calculated={interest}")

            if locked_count == 0:
                print("No locked vaults found!")
                return False

            # Debug house balance access

            
            # Check if house can afford interest
            house_balance = int(self.currency.get(str(house_id), 0))  # Convert ID to string
            print(f"House ID: {house_id}")
            print(f"House balance found: {house_balance}")
            
            if house_balance < total_interest:
                print(f"WARNING: House cannot afford interest payments! Need: {total_interest}, Have: {house_balance}")
                return False

            # Second pass: Apply interest to each locked vault
            print("\nApplying interest payments...")
            for user_id, data in vault_data.items():
                if data.get("locked", False):
                    current_balance = data.get("balance", 0)
                    interest = int(current_balance * 0.0025)
                    new_balance = current_balance + interest
                    vault_data[user_id]["balance"] = new_balance
                    print(f"User {user_id}: Old balance={current_balance}, Interest={interest}, New balance={new_balance}")

            # Update house balance and save everything
            self.currency[str(house_id)] = house_balance - total_interest  # Convert ID to string
            print(f"\nUpdating house balance: {house_balance} -> {self.currency[str(house_id)]}")
            
            self.save_vault_data(vault_data)
            self.save_currency()
            print(" ")
            print("=== Interest Payment Completed ===")
            return True

        except Exception as e:
            print(f"ERROR in interest payment for {payment_time}: {e}")
            import traceback
            traceback.print_exc()
            return False

    @tasks.loop(time=time(hour=12, minute=30, second=15))
    async def interest_task(self):
        await asyncio.sleep(10)
        try:
            print(" ")
            print("\n=== Interest Task Check ===")
            last_interest_time = self.load_last_interest_time()
            now = datetime.now()
            time_elapsed = now - last_interest_time
            required_delay = timedelta(hours=24)

            print(f"Last interest time: {last_interest_time}")
            print(f"Current time: {now}")
            print(f"Time elapsed: {time_elapsed}")
            
            # Calculate how many payments were missed
            missed_payments = int(time_elapsed.total_seconds() // required_delay.total_seconds())
            print(f"Missed payments: {missed_payments}")
            
            if missed_payments > 0:
                print(f"Found {missed_payments} missed payment(s)")
                
                # Process each missed payment
                for i in range(missed_payments):
                    payment_time = last_interest_time + (required_delay * (i + 1))
                    
                    # Don't process future payments
                    if payment_time > now:
                        print(f"Skipping future payment time: {payment_time}")
                        break
                    
                    print(f"\nProcessing payment {i+1}/{missed_payments} for timestamp: {payment_time}")
                    if await self.process_interest_payment(payment_time):
                        self.save_last_interest_time(payment_time)
                        print(f"Successfully processed payment for {payment_time}")
                    else:
                        print(f"Failed to process payment for {payment_time}")
                        break
            else:
                print("No interest payments due yet")

        except Exception as e:
            print(f"Interest task error: {e}")
            import traceback
            traceback.print_exc()





        


    @vault.command(name="lock")
    async def vault_lock(self, ctx):
        """Lock your vault"""
        try:
            user_id = str(ctx.author.id)
            vault_data = self.load_vault_data()

            # Check if user has a vault and minimum balance
            if user_id not in vault_data:
                await ctx.send("You don't have a vault yet!")
                return

            if vault_data[user_id]["balance"] < 500000:
                await ctx.send("You need at least 500k in your vault to lock it!")
                return

            # Check if already locked
            if vault_data[user_id].get("locked", False):
                lock_until = datetime.fromtimestamp(vault_data[user_id]["lock_until"])
                if lock_until > datetime.now():
                    remaining = lock_until - datetime.now()
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    embed = discord.Embed(
                        title="🔒 Vault Already Locked",
                        description=f"Your vault is already locked!\nUnlocks in: {hours}h {minutes}m",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

            # Create informational embed
            info_embed = discord.Embed(
                title="🔒 Vault Lock Information",
                description=(
                    "Locking your vault prevents withdrawals until the lock expires.\n\n"
                    "**Benefits:**\n"
                    "• Earn interest while locked\n"
                    "• Force yourself to save\n\n"
                    "**Warning:**\n"
                    "• Early unlock costs 10% of vault balance\n"
                    "• Requires 50M minimum balance to unlock early\n"
                    "• Lock duration cannot be shortened once set\n\n"
                    "Choose your lock duration:"
                ),
                color=discord.Color.gold()
            )

            class LockDurationView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=30)
                    self.value = None

                @discord.ui.button(label="12 Hours", style=discord.ButtonStyle.blurple)
                async def hour(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = timedelta(hours=12)
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                @discord.ui.button(label="3 Days", style=discord.ButtonStyle.blurple)
                async def day(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = timedelta(days=3)
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                @discord.ui.button(label="1 Week", style=discord.ButtonStyle.blurple)
                async def week(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = timedelta(weeks=1)
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                @discord.ui.button(label="Custom Time", style=discord.ButtonStyle.gray)
                async def custom(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    
                    modal = DayInput(self)
                    await interaction.response.send_modal(modal)

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = None
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                def disable_all_buttons(self):
                    for item in self.children:
                        item.disabled = True

            view = LockDurationView()
            message = await ctx.send(embed=info_embed, view=view)

            # Wait for button interaction
            await view.wait()
            
            if view.value:
                lock_duration = view.value
                lock_until = datetime.now() + lock_duration
                
                # Save lock data
                vault_data[user_id]["locked"] = True
                vault_data[user_id]["lock_until"] = lock_until.timestamp()
                self.save_vault_data(vault_data)

                # Calculate when it unlocks
                hours = int(lock_duration.total_seconds() // 3600)
                minutes = int((lock_duration.total_seconds() % 3600) // 60)

                success_embed = discord.Embed(
                    title="🔒 Vault Locked Successfully",
                    description=(
                        f"Your vault has been locked for: **{hours}h {minutes}m**\n\n"
                        f"Unlocks on: {lock_until.strftime('%Y-%m-%d %H:%M')}\n"
                        f"Current Balance: <:goldpoints:1319902464115343473> {self.format_amount(vault_data[user_id]['balance'])}"
                    ),
                    color=discord.Color.green()
                )
                await message.edit(embed=success_embed, view=None)
            else:
                cancel_embed = discord.Embed(
                    title="<:remove:1328511957208268800>  Lock Cancelled",
                    description="Your vault remains unlocked.",
                    color=discord.Color.red()
                )
                await message.edit(embed=cancel_embed, view=None)

        except Exception as e:
            print(f"Lock error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")


    @vault.command(name="unlock")
    async def vault_unlock(self, ctx):
        """Emergency unlock your vault (10% fee, minimum 50M balance required)"""
        try:
            user_id = str(ctx.author.id)
            vault_data = self.load_vault_data()
            house_id = "1233966655923552370" 
            # Check if user has a vault
            if user_id not in vault_data:
                await ctx.send("You don't have a vault yet!")
                return

            # Check if vault is actually locked
            if not vault_data[user_id].get("locked", False):
                await ctx.send("Your vault is not locked!")
                return

            # Check minimum balance requirement
            current_balance = vault_data[user_id]["balance"]
            if current_balance < 50000000:  # 50M minimum
                await ctx.send("You need at least 50M in your vault to use emergency unlock!")
                return

            # Calculate 10% fee
            fee = int(current_balance * 0.10) 
            if fee != vault_data[user_id]['balance']:
                print(f"Fee: {fee}")
                print(f"Current vault balance: {vault_data[user_id]['balance']}")
            class UnlockConfirmView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=30)
                    self.value = None

                @discord.ui.button(label="Confirm Unlock", style=discord.ButtonStyle.green, emoji="✅")
                async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = True
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
                async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This is not your vault!", ephemeral=True)
                        return
                    self.value = False
                    self.disable_all_buttons()
                    await interaction.response.edit_message(view=self)
                    self.stop()

                def disable_all_buttons(self):
                    for item in self.children:
                        item.disabled = True

            view = UnlockConfirmView()
            embed = discord.Embed(
                title="🔓 Emergency Unlock",
                description=f"Are you sure you want to unlock your vault?\n\n"
                        f"Current Balance: <:goldpoints:1319902464115343473> {self.format_amount(current_balance)}\n"
                        f"Unlock Fee (10%): <:goldpoints:1319902464115343473> {self.format_amount(fee)}\n"
                        f"Final Balance: <:goldpoints:1319902464115343473> {self.format_amount(current_balance - fee)}",
                color=discord.Color.gold()
            )
            message = await ctx.send(embed=embed, view=view)

            # Wait for button interaction
            await view.wait()
            
            if view.value is True:
                # Apply fee
                vault_data[user_id]["balance"] -= fee
                # Unlock vault
                vault_data[user_id]["locked"] = False
                vault_data[user_id]["lock_until"] = None
                # Save the changes
                print(f"House balance before: {self.currency.get(house_id, 0)}")
                self.currency[house_id] = self.currency.get(house_id, 0) + fee
                self.save_vault_data(vault_data)
                self.save_currency()
                print(f"House balance after: {self.currency[house_id]}")

                success_embed = discord.Embed(
                    title="🔓 Vault Unlocked",
                    description=f"Your vault has been unlocked!\n\n"
                            f"Fee Paid: <:goldpoints:1319902464115343473> {self.format_amount(fee)}\n"
                            f"New Balance: <:goldpoints:1319902464115343473> {self.format_amount(vault_data[user_id]['balance'])}",
                    color=discord.Color.green()
                )
                await message.edit(embed=success_embed, view=None)
            elif view.value is False:
                cancel_embed = discord.Embed(
                    title="<:remove:1328511957208268800>  Unlock Cancelled",
                    description="Your vault remains locked.",
                    color=discord.Color.red()
                )
                await message.edit(embed=cancel_embed, view=None)
            else:
                timeout_embed = discord.Embed(
                    title="⏰ Unlock Timed Out",
                    description="No response received. Your vault remains locked.",
                    color=discord.Color.red()
                )
                await message.edit(embed=timeout_embed, view=None)

        except Exception as e:
            print(f"Unlock error: {e}")
            await ctx.send(f"An error occurred: {str(e)}")

    def save_vault_data(self, data):
        """Save vault data to JSON file"""
        with open('.json/vaults.json', 'w') as f:
            json.dump(data, f, indent=4)

    def load_vault_data(self):
        """Load vault data from JSON file"""
        try:
            with open('.json/vaults.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}







async def setup(bot):
    await bot.add_cog(Economy(bot))
