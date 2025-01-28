import discord
from discord.ext import commands
import json
import os

class HouseProfits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def load_json(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON error in {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return {}

    def analyze_house_transactions(self, data, house_balance):
        transactions = data.get("users", {}).get("HOUSE", {}).get("transactions", [])
        
        total_deposits = 0
        total_withdrawals = 0
        initial_balance = 0

        for entry in transactions:
            txn = entry["transaction"]
            amount = txn["amount"]
            txn_type = txn["type"]
            
            if txn_type == "add":
                total_deposits += amount
            elif txn_type == "remove":
                total_withdrawals += amount
            
            initial_balance += amount if txn_type == "add" else -amount

        final_balance = house_balance
        profit_or_loss = final_balance - initial_balance
        gain_loss_percentage = (profit_or_loss / initial_balance) * 100 if initial_balance != 0 else 0

        profit_or_loss_str = f"{'+' if profit_or_loss >= 0 else '-'}{abs(profit_or_loss):,}"
        gain_loss_percentage_str = f"{'+' if gain_loss_percentage >= 0 else '-'}{abs(gain_loss_percentage):.2f}%"

        return {
            "initial_balance": initial_balance,
            "final_balance": final_balance,
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "profit_or_loss": profit_or_loss_str,
            "gain_loss_percentage": gain_loss_percentage_str
        }

    @commands.command(name="houseprofits", aliases=["profit", "profits", "houseprofit"])
    @commands.has_permissions(administrator=True)  # Only administrators can use this command
    async def house_profits(self, ctx):
        """Display house profit statistics"""
        
        # Load the house balance from currency.json
        currency_data = self.load_json('.json/currency.json')
        house_balance = currency_data.get('1233966655923552370', 0)

        # Load transaction data
        transaction_data = self.load_json('./logs/transactions.json')

        if not transaction_data or not house_balance:
            await ctx.send("No data to analyze or invalid data found.")
            return

        results = self.analyze_house_transactions(transaction_data, house_balance)

        # Create an embed for better presentation
        embed = discord.Embed(
            title="House Profits Analysis",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Balance Information",
            value=f"Initial Balance: {results['initial_balance']:,}\n"
                  f"Final Balance: {results['final_balance']:,}",
            inline=False
        )

        embed.add_field(
            name="Transaction Summary",
            value=f"Total Deposits: +{results['total_deposits']:,}\n"
                  f"Total Withdrawals: -{results['total_withdrawals']:,}",
            inline=False
        )

        embed.add_field(
            name="Profit Analysis",
            value=f"Profit/Loss: {results['profit_or_loss']}\n"
                  f"Gain/Loss: {results['gain_loss_percentage']}",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HouseProfits(bot))
