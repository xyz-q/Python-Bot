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
from pathlib import Path
import functools
from datetime import datetime
import copy
import typing




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



# Modified transaction_limit function
def transaction_limit():
    async def predicate(ctx):
        try:
            args = ctx.message.content.split()
            
            if len(args) <= 1:
                return True
                
            amount = None
            for arg in args[1:]:
                try:
                    cleaned_arg = arg.strip('$,k,m,b,K,M,B')
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

            if amount is None:
                return True

            if amount < limits_manager.current_min:
                await ctx.send(f"Amount too low! Minimum amount is {limits_manager.current_min:,} <:goldpoints:1319902464115343473>")
                return False
            
            if amount > limits_manager.current_max:
                await ctx.send(f"Amount too high! Maximum amount is {limits_manager.current_max:,} <:goldpoints:1319902464115343473>")
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

            # Step 1: Convert the amount if it's given as a string with a suffix (k, m, b)
            try:
                amount = str(amount).lower().replace(',', '').replace(' ', '')
                multipliers = {
                    'k': 1_000,
                    'm': 1_000_000,
                    'b': 1_000_000_000
                }

                if amount[-1] in multipliers:
                    number = float(amount[:-1])
                    multiplier = multipliers[amount[-1]]
                    amount = int(number * multiplier)
                else:
                    amount = int(float(amount))

                print(f"Converted amount: {amount}")

            except (ValueError, TypeError):
                await ctx.send("Invalid amount format!", delete_after=10)
                return None

            # Step 2: Check if the amount is valid (positive and within user balance)
            if amount <= 0:
                await ctx.send("Amount must be positive!", delete_after=10)
                return None

            balance = await self.get_balance(ctx.author.id)
            print(f"User balance: {balance}")

            if amount > balance:
                await ctx.send(f"You don't have enough coins! Your balance: {self.format_amount(amount)} <:goldpoints:1319902464115343473> ", delete_after=10)
                return None

            # Step 3: If the amount exceeds the threshold, trigger the confirmation
            if amount >= self.CONFIRMATION_THRESHOLD:
                print(f"Amount exceeds threshold: {self.CONFIRMATION_THRESHOLD}")
                view = BetConfirmation()  # Assuming this is a button or modal view
                message = await ctx.send(
                    f"⚠️ Are you sure you want to use {amount:,} <:goldpoints:1319902464115343473>?", 
                    view=view
                )

                await view.wait()

                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

                if view.value is None:
                    await ctx.send("Warning timed out!", delete_after=10)
                    return None
                elif view.value is False:
                    await ctx.send("Cancelled!", delete_after=10)
                    return None

                print("Bet confirmed!")

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
    MAX_TRANSACTION_AMOUNT = 1_000_000_000  # 5B maximum
    def __init__(self, bot):
        self.bot = bot
        self.current_author = None
        self.currency = {}
        self.load_currency()
        self.balances = {}
        self.stats = {}
        self.load_stats()  
        self.admin_id = 110927272210354176
        

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

    @commands.command(name="resetstats")
    async def reset_stats(self, ctx, user: discord.Member = None):
        if user and not ctx.author.guild_permissions.administrator:
            await ctx.send("Only administrators can reset other users' stats!")
            return
            
        target_user = user or ctx.author
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
        
        await ctx.send(f"📊 Statistics have been reset for {target_user.name}!")

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

    def parse_amount(self, amount):
        """Convert string amounts like '5k', '1m', etc. to integers"""
        if isinstance(amount, (int, float)):
            return int(amount)
            
        amount = str(amount).lower().strip()
        multipliers = {
            'k': 1000,
            'm': 1000000,
            'b': 1000000000,
            't': 1000000000000
        }
        
        try:
            if amount[-1] in multipliers:
                number = float(amount[:-1])
                return int(number * multipliers[amount[-1]])
            return int(float(amount))
        except (ValueError, IndexError):
            return 0

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
    @confirm_bet()

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
    @confirm_bet()

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
                color=discord.Color.red()
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
            house_id = "1233966655923552370"

            # Verify both players have enough balance
            if challenger_balance < bet_amount:
                await ctx.send(f"You don't have enough balance! Your balance: <:goldpoints:1319902464115343473> {self.format_amount(challenger_balance)}")
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



    @commands.command(name="slots", aliases=["gamble", "slot"])
    @confirm_bet()

    @transaction_limit()
    async def slots(self, ctx, amount: str = None):
        # Define slot machine symbols with weights and multipliers (total weight = 100)
        symbols = self.symbols
        
        # Create weighted symbol list
        weighted_symbols = []
        for symbol, data in symbols.items():
            weighted_symbols.extend([symbol] * data["weight"])

        user_id = ctx.author.id
        initial_amount = amount         
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
            # Parse bet amount and get balances
            bet = self.parse_amount(amount)
            user_id = str(ctx.author.id)
            house_id = str(self.bot.user.id)
            user_balance = await self.get_balance(user_id)
            
            if house_id not in self.currency:
                self.currency[house_id] = 0   

            # Validate bet and balances
            if bet <= 0:
                await ctx.send("You must bet at least 1 coin!")
                return
                    
            if bet > user_balance:
                await ctx.send(f"You don't have enough coins! Your balance: {self.format_amount(user_balance)} <:goldpoints:1319902464115343473> ")
                return

            # Check house balance
            house_balance = int(self.currency[house_id])
            max_possible_win = bet * 30  # Maximum possible win (Diamond 30x)
            if house_balance < max_possible_win:
                await ctx.send("The house doesn't have enough balance to cover potential winnings! Please try a smaller bet.")
                return

            # Deduct bet ONCE at the start
            print(f"taking {bet} from {user_id}")
            self.currency[user_id] -= bet
            print(f"giving {bet} to house")
            self.currency[house_id] += bet
            while_betting_balance = await self.get_balance(user_id)
            # Create and send initial embed
            embed = discord.Embed(title="<:gamba:1328512027282374718> Slot Machine <:gamba:1328512027282374718>", color=discord.Color.gold())
            embed.add_field(name="Spinning...", value="| ❓ | ❓ | ❓ |")
            embed.set_footer(text=f"Balance: {self.format_amount(while_betting_balance)} GP")
            msg = await ctx.send(embed=embed)

            # Generate final results

            
            guaranteed_match = random.random() < 0.1  # 15% chance for a guaranteed match
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
                gross_win = bet * multiplier
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                win_amount = gross_win - tax_amount
                
                # Add winnings (bet already deducted)
                print(f"adding {winnings} to {user_id} from a 3 of a kind!")
                self.currency[user_id] += winnings
                print(f"subtracting {winnings} from house")
                self.currency[house_id] -= winnings
                
                # Get final balance after transaction
                final_balance = int(self.currency[user_id])
                
                result = f"🎉 JACKPOT! Triple {symbols[symbol]['name']}! 🎉"
                await self.log_transaction(ctx, self.parse_amount(amount), win_amount, final_balance, is_house=False)
                
            elif max_matches == 2:
                matching_symbol = [s for s, count in symbol_counts.items() if count == 2][0]
                base_multiplier = symbols[matching_symbol]["multiplier"]
                multiplier = base_multiplier * 0.4
                gross_win = int(bet * multiplier)
                tax_amount = int(gross_win * 0.05)
                winnings = gross_win - tax_amount
                win_amount = gross_win - tax_amount
                
                # Add winnings (bet already deducted)
                print(f"adding {winnings} to {user_id} from a 2 of a kind!")
                self.currency[user_id] += winnings
                print(f"subtracting {winnings} from house")
                self.currency[house_id] -= winnings
                
                # Get final balance after transaction
                final_balance = int(self.currency[user_id])
                
                result = f"🎈 Double {symbols[matching_symbol]['name']}! 🎈"
                await self.log_transaction(ctx, self.parse_amount(amount), win_amount, final_balance, is_house=False)
                
            else:
                winnings = 0
                # Get final balance after bet was deducted
                final_balance = int(self.currency[user_id])
                bet_amount = self.parse_amount(amount)
                tax_amount = 0
                result = "No match!"
                print(f"house wins! house keeps the {bet_amount} gp!")
                await self.log_transaction(ctx, bet_amount, -bet_amount, final_balance, is_house=False)
                # No need to do anything here, bet was already deducted

            # Update stats and save
            self.update_stats(user_id, bet, winnings)
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
                value=f"Bet: {self.format_amount(bet)}\n"
                    f"Win: +{self.format_amount(winnings)}\n"
                    f"Tax: {self.format_amount(tax_amount)}",
                inline=False
            )
            
            result_embed.set_footer(
                text=f"New Balance: {self.format_amount(await self.get_balance(user_id))} GP"
            )

            await msg.edit(embed=result_embed)

        except Exception as e:
            print(f"Error: {e}")
            await ctx.send("An error occurred while processing your bet.")




    @commands.command(aliases=["stake", "flowers"])

    @transaction_limit()
    @confirm_bet()
    async def flower(self, ctx, bet_amount: str = None):
        user_id = ctx.author.id
        initial_amount = self.parse_amount(bet_amount)
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
            amount = self.parse_amount(bet_amount)
            if amount <= 0:
                await ctx.send("Please enter a valid bet amount!")
                return
            house_id = str(self.bot.user.id)
            if house_id not in self.currency:
                self.currency[house_id] = 0      
  


            max_possible_win = amount * 2  # Assuming bet is already parsed
            if int(self.currency[house_id]) < max_possible_win:
                await ctx.send("The house doesn't have enough balance to cover potential winnings! Please try a smaller bet.")
                return             

            # Check if user has enough balance
            user_id = str(ctx.author.id)
            if user_id not in self.currency:
                self.currency[user_id] = 0

            print(f"taking {amount} from {user_id} for flower game")
            self.currency[user_id] -= amount
            print(f"giving {amount} to house")
            self.currency[house_id] += amount 
            self.save_currency()             
            
            if self.currency[user_id] < amount:
                await ctx.send(f"You don't have enough balance for this bet! Your balance: {self.format_amount(await self.get_balance(user_id))} <:goldpoints:1319902464115343473>")
                return

  

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
                player_hand.append(p_value)
                player_flowers[i] = p_flower

                # Clear previous fields and update the embed
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
                    winnings = amount * 1.90
                    self.update_stats(user_id, amount, winnings)
                else:
                    self.currency[user_id] += amount  # Player wins
                
                self.save_currency()
                return

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
                                        
                print(f"banker wins {amount} GP! from double 9s!")
                self.update_stats(user_id, amount, 0)
                final_balance = await self.get_balance(user_id)
                await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)
                
                final_embed.set_footer(
                    text=f"New Balance: {self.format_amount(final_balance)} GP"
                )

            elif player_total > banker_total:
                # Player wins
                winnings = amount * 2
                tax_amount = int(winnings * 0.05)
                net_winnings = winnings - tax_amount
                self.currency[user_id] += net_winnings
                self.update_stats(user_id, amount, net_winnings)
                print(f"Player wins {winnings} GP, tax: {tax_amount}, net: {net_winnings}")
                self.currency[house_id] -= winnings
                self.currency[house_id] += tax_amount
                
                final_balance = await self.get_balance(user_id)
                await self.log_transaction(ctx, amount, net_winnings, final_balance, is_house=False)
                
                final_embed.add_field(
                    name="Result", 
                    value=f"You win! <a:MUGA:1178140574570790954>\nWinnings: {self.format_amount(net_winnings)} (After 5% tax)", 
                    inline=False
                )
                final_embed.set_footer(
                    text=f"New Balance: {self.format_amount(final_balance)} GP"
                )
                                        
            elif banker_total > player_total:
                # Banker wins

                self.update_stats(user_id, amount, 0)
                print(f"banker wins {amount} GP! from banker win!")
                final_balance = await self.get_balance(user_id)
                await self.log_transaction(ctx, amount, -amount, final_balance, is_house=False)
                
                final_embed.add_field(
                    name="Result", 
                    value="Banker wins! <a:xdd:1221066292631568456>", 
                    inline=False
                )
                final_embed.set_footer(
                    text=f"New Balance: {self.format_amount(final_balance)} GP"
                )                

            else:
                # Tie
                
                print(f"Tie! Refunding bet: {amount}")
                self.currency[user_id] += amount  # Refund the bet on a tie
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
                    text=f"New Balance: {self.format_amount(final_balance)} GP"
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
    @commands.has_permissions(administrator=True)  # Only admins can change limits
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
            def parse_amount(amount_str):
                amount_str = amount_str.lower().strip('$,')
                if 'k' in amount_str:
                    return float(amount_str.replace('k', '')) * 1000
                elif 'm' in amount_str:
                    return float(amount_str.replace('m', '')) * 1000000
                elif 'b' in amount_str:
                    return float(amount_str.replace('b', '')) * 1000000000
                return float(amount_str)

            new_min = parse_amount(min_amount)
            new_max = parse_amount(max_amount)

            # Validation
            if new_min <= 0 or new_max <= 0:
                await ctx.send("❌ Limits must be positive numbers!")
                return

            if new_min >= new_max:
                await ctx.send("❌ Minimum limit must be less than maximum limit!")
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
            await ctx.send("❌ Invalid amount format! Use numbers with optional k, m, or b suffix (e.g., 500k, 1m)")

    @set_limits.error
    async def limits_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to change limits!")



    @commands.command(name="setbalance", aliases=["setbal", "set"])
    @commands.is_owner() 
    async def set_balance(self, ctx, member: discord.Member, amount: str):
        """Set a user's balance to a specific amount"""
        try:
            # Parse the amount (supporting k, m, b notation)
            def parse_amount(amount_str):
                amount_str = amount_str.lower().strip('$,')
                if 'k' in amount_str:
                    return float(amount_str.replace('k', '')) * 1000
                elif 'm' in amount_str:
                    return float(amount_str.replace('m', '')) * 1000000
                elif 'b' in amount_str:
                    return float(amount_str.replace('b', '')) * 1000000000
                elif 't' in amount_str:
                    return float(amount_str.replace('t', '')) * 1000000000000
                return float(amount_str)

            new_balance = parse_amount(amount)
            user_id = str(member.id)
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
                value=f"{member.mention}", 
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
            
            # Log the transaction


        except ValueError:
            await ctx.send("❌ Invalid amount format! Use numbers with optional k, m, or b suffix (e.g., 500k, 1m)")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @set_balance.error
    async def set_balance_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to set balances!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage: ,setbalance <@user> <amount>")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Could not find that user!")



async def setup(bot):
    await bot.add_cog(Economy(bot))
