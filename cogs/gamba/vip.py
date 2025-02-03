import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta

class VIPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vip_data_file = ".json/vip_data.json"
        self.levels_file = ".json/levels.json"
        self.user_levels_file = ".json/user_levels.json"  # File where user levels are stored
        
        self.vip_tiers = {
            "basic": {
                "price": 1000000,
                "period": 30,  # days
                "perks": ["VIP Status", "VIP Commands", "Special Icon"]
            },
            "premium": {
                "price": 2000000,
                "period": 30,
                "perks": ["VIP Status", "VIP Commands", "Special Icon", "Extra Perks"]
            }
        }
        
        self.vip_data = self.load_vip_data()
        self.check_subscriptions.start()

    async def process_vip_payment(self, user_id: str, amount: int):
        """Process VIP payment and add to house/bot balance"""
        BOT_ID = "1233966655923552370"  # House balance ID
        
        try:
            # Load currency data
            with open('.json/currency.json', 'r') as f:
                currency_data = json.load(f)
            
            # Check user balance
            user_balance = int(currency_data.get(user_id, 0))
            if user_balance < amount:
                return False
                
            # Deduct from user
            currency_data[user_id] = user_balance - amount
            
            # Add to bot/house balance
            bot_balance = int(currency_data.get(BOT_ID, 0))
            currency_data[BOT_ID] = bot_balance + amount
            
            # Save changes
            with open('.json/currency.json', 'w') as f:
                json.dump(currency_data, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error processing VIP payment: {e}")
            return False



    def load_vip_data(self):
        try:
            with open(self.vip_data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_vip_data(self):
        with open(self.vip_data_file, 'w') as f:
            json.dump(self.vip_data, f, indent=4)

    def load_user_levels(self):
        try:
            with open(self.user_levels_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_user_levels(self, user_levels):
        with open(self.user_levels_file, 'w') as f:
            json.dump(user_levels, f, indent=4)

    async def update_user_level(self, user_id: str, is_vip: bool):
        try:
            with open('.json/special_levels.json', 'r') as f:
                special_levels = json.load(f)
            
            if is_vip:
                # Add user to special levels with VIP level (-2)
                special_levels[user_id] = -2
            else:
                # Remove user from special levels if they exist
                if user_id in special_levels:
                    del special_levels[user_id]
            
            # Save the updated special levels
            with open('.json/special_levels.json', 'w') as f:
                json.dump(special_levels, f, indent=4)
                
        except FileNotFoundError:
            # If file doesn't exist, create it with the user if they're VIP
            special_levels = {user_id: -2} if is_vip else {}
            with open('.json/special_levels.json', 'w') as f:
                json.dump(special_levels, f, indent=4)


    @commands.group(name="vip")
    async def vip(self, ctx):
        """VIP membership commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand: subscribe, status, tiers, cancel")

    @vip.command(name="tiers")
    async def show_tiers(self, ctx):
        """Display available VIP tiers"""
        embed = discord.Embed(title="VIP Membership Tiers", color=discord.Color.gold())
        
        for tier, data in self.vip_tiers.items():
            perks_text = "\n".join(f"• {perk}" for perk in data['perks'])
            embed.add_field(
                name=f"{tier.capitalize()} - {data['price']:,} coins/month",
                value=f"Perks:\n{perks_text}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @vip.command(name="subscribe")
    async def subscribe(self, ctx, tier: str):
        """Subscribe to a VIP tier"""
        tier = tier.lower()
        if tier not in self.vip_tiers:
            await ctx.send("Invalid tier! Use `!vip tiers` to see available tiers.")
            return

        tier_price = self.vip_tiers[tier]['price']
        
        # Process payment
        if not await self.process_vip_payment(str(ctx.author.id), tier_price):
            await ctx.send(f"Insufficient funds! You need {tier_price:,} coins.")
            return

        # Update VIP status
        self.vip_data[str(ctx.author.id)] = {
            "tier": tier,
            "start_date": datetime.now().isoformat(),
            "next_payment": (datetime.now() + timedelta(days=self.vip_tiers[tier]['period'])).isoformat()
        }
        self.save_vip_data()

        # Update user's level to VIP (-2)
        await self.update_user_level(str(ctx.author.id), True)
        
        await ctx.send(f"Successfully subscribed to {tier.capitalize()} VIP tier!")


    @vip.command(name="status")
    async def check_status(self, ctx):
        """Check your VIP status"""
        user_id = str(ctx.author.id)
        if user_id not in self.vip_data:
            await ctx.send("You don't have an active VIP subscription.")
            return

        vip_info = self.vip_data[user_id]
        next_payment = datetime.fromisoformat(vip_info['next_payment'])
        
        embed = discord.Embed(title="VIP Status", color=discord.Color.blue())
        embed.add_field(name="Current Tier", value=vip_info['tier'].capitalize())
        embed.add_field(name="Next Payment", value=next_payment.strftime("%Y-%m-%d"))
        embed.add_field(name="Monthly Cost", value=f"{self.vip_tiers[vip_info['tier']]['price']:,} coins")
        
        await ctx.send(embed=embed)

    @vip.command(name="cancel")
    async def cancel_subscription(self, ctx):
        """Cancel your VIP subscription"""
        user_id = str(ctx.author.id)
        if user_id not in self.vip_data:
            await ctx.send("You don't have an active VIP subscription.")
            return

        del self.vip_data[user_id]
        self.save_vip_data()
        
        # Remove VIP status and update level
        await self.update_user_level(user_id, False)
        
        await ctx.send("Your VIP subscription has been cancelled.")

    @tasks.loop(hours=8)
    async def check_subscriptions(self):
        """Check and process subscription renewals"""
        current_time = datetime.now()
        
        for user_id, data in list(self.vip_data.items()):
            next_payment = datetime.fromisoformat(data['next_payment'])
            
            if current_time >= next_payment:
                tier_price = self.vip_tiers[data['tier']]['price']

                # Process payment
                if await self.process_vip_payment(user_id, tier_price):
                    # Update next payment date
                    self.vip_data[user_id]['next_payment'] = (
                        next_payment + timedelta(days=self.vip_tiers[data['tier']]['period'])
                    ).isoformat()
                    self.save_vip_data()
                else:
                    # Cancel subscription due to insufficient funds
                    del self.vip_data[user_id]
                    self.save_vip_data()
                    
                    # Remove VIP status
                    await self.update_user_level(user_id, False)
                    
                    try:
                        user = self.bot.get_user(int(user_id))
                        if user:
                            await user.send("Your VIP subscription has been cancelled due to insufficient funds.")
                    except discord.HTTPException:
                        pass


async def setup(bot):
    await bot.add_cog(VIPSystem(bot))
