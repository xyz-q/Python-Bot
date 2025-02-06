import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import discord
from discord.ui import Button, View
from discord.ext import commands
import asyncio

class VIPView(View):
    def __init__(self, cog, ctx, is_subscribed=False):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.is_subscribed = is_subscribed
        self.message = None

        # Add subscription-specific buttons
        if not is_subscribed:
            subscribe_button = Button(
                label="Subscribe to VIP", 
                style=discord.ButtonStyle.green,
                custom_id="subscribe"
            )
            subscribe_button.callback = self.subscribe_callback
            self.add_item(subscribe_button)
        else:
            status_button = Button(
                label="Check Status", 
                style=discord.ButtonStyle.blurple,
                custom_id="status"
            )
            status_button.callback = self.status_callback
            self.add_item(status_button)

            cancel_button = Button(
                label="Cancel VIP", 
                style=discord.ButtonStyle.gray,
                custom_id="cancel"
            )
            cancel_button.callback = self.cancel_callback
            self.add_item(cancel_button)

        # Add close button (appears for everyone)
        close_button = Button(
            label="✖", 
            style=discord.ButtonStyle.red,
            custom_id="close"
        )
        close_button.callback = self.close_callback
        self.add_item(close_button)

    async def close_callback(self, interaction: discord.Interaction):
        # Delete the message with the view
        await interaction.message.delete()





    async def on_timeout(self):
        """Called when the view times out"""
        if self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass

    async def subscribe_callback(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu!", ephemeral=True, delete_after=8)
            return

        vip_price = self.cog.vip_price
        
        if not await self.cog.process_vip_payment(str(interaction.user.id), vip_price):
            await interaction.response.send_message(f"Insufficient funds! You need {vip_price:,} coins.", ephemeral=True, delete_after=8)
            return

        self.cog.vip_data[str(interaction.user.id)] = {
            "start_date": datetime.now().isoformat(),
            "next_payment": (datetime.now() + timedelta(days=30)).isoformat()
        }
        self.cog.save_vip_data()

        await self.cog.update_user_level(str(interaction.user.id), True)
        
        await interaction.response.send_message("Successfully subscribed to VIP!", ephemeral=True, delete_after=8)
        await self.update_vip_message(interaction)

    async def status_callback(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu!", ephemeral=True, delete_after=8)
            return

        vip_info = self.cog.vip_data[str(interaction.user.id)]
        next_payment = datetime.fromisoformat(vip_info['next_payment'])
        
        embed = discord.Embed(title="VIP Status", color=discord.Color.gold())
        embed.add_field(name="Monthly Cost", value=f"{self.cog.vip_price:,} coins")
        embed.add_field(name="Next Payment", value=next_payment.strftime("%Y-%m-%d"))
        embed.add_field(name="Perks", value="\n".join(f"• {perk}" for perk in self.cog.vip_perks), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=8)

    async def cancel_callback(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu!", ephemeral=True, delete_after=8)
            return

        user_id = str(interaction.user.id)
        if user_id in self.cog.vip_data:
            del self.cog.vip_data[user_id]
            self.cog.save_vip_data()
            await self.cog.update_user_level(user_id, False)
            await interaction.response.send_message("Your VIP subscription has been cancelled.", ephemeral=True, delete_after=8)
            await self.update_vip_message(interaction)
        else:
            await interaction.response.send_message("You don't have an active subscription!", ephemeral=True, delete_after=8)

    async def update_vip_message(self, interaction):
        is_subscribed = str(interaction.user.id) in self.cog.vip_data
        embed = await self.cog.create_vip_embed(interaction.user, is_subscribed)
        new_view = VIPView(self.cog, self.ctx, is_subscribed)
        await interaction.message.edit(embed=embed, view=new_view)


class VIPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vip_data_file = ".json/vip_data.json"
        self.vip_price = 75000000
        self.vip_perks = [
            "VIP Role",
            "Support the bot!",
            "[COMING SOON] Weekly Drops",
            "[COMING SOON] Reduce Cooldowns",
            "Priority Support",
            "Discord access"
        ]
        self.vip_data = self.load_vip_data()
        self.check_subscriptions.start()

    async def process_vip_payment(self, user_id: str, amount: int):
        """Process VIP payment and add to house/bot balance"""
        BOT_ID = "1233966655923552370"
        
        try:
            economy_cog = self.bot.get_cog('Economy')
            if not economy_cog:
                print("Economy cog not found!")
                return False

            user_balance = await economy_cog.get_balance(user_id)
            
            print(f"\nProcessing VIP Payment:")
            print(f"User {user_id} current balance: {user_balance:,}")
            print(f"House current balance: {await economy_cog.get_balance(BOT_ID):,}")
            print(f"Payment amount: {amount:,}")

            if user_balance < amount:
                return False
                
            economy_cog.currency[str(user_id)] = user_balance - amount
            economy_cog.currency[BOT_ID] = economy_cog.currency.get(BOT_ID, 0) + amount
            
            if hasattr(economy_cog, 'save_currency'):
                economy_cog.save_currency()
            else:
                with open('.json/currency.json', 'w') as f:
                    json.dump(economy_cog.currency, f, indent=4)
            
            print(f"\nNew balances:")
            print(f"User: {await economy_cog.get_balance(user_id):,}")
            print(f"House: {await economy_cog.get_balance(BOT_ID):,}")
            
            return True
            
        except Exception as e:
            print(f"Error in process_vip_payment: {e}")
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
                special_levels[user_id] = -2
            else:
                if user_id in special_levels:
                    del special_levels[user_id]
            
            with open('.json/special_levels.json', 'w') as f:
                json.dump(special_levels, f, indent=4)
                
        except FileNotFoundError:
            special_levels = {user_id: -2} if is_vip else {}
            with open('.json/special_levels.json', 'w') as f:
                json.dump(special_levels, f, indent=4)

    async def create_vip_embed(self, user, is_subscribed):
        if is_subscribed:
            vip_info = self.vip_data[str(user.id)]
            embed = discord.Embed(
                title="🌟 VIP Membership Status", 
                description="Your current VIP subscription information:", 
                color=discord.Color.gold()
            )
            next_payment = datetime.fromisoformat(vip_info['next_payment'])
            embed.add_field(name="Status", value="Active VIP Member", inline=True)
            embed.add_field(name="Next Payment", value=next_payment.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Monthly Cost", value=f"{self.vip_price:,} coins", inline=False)
            embed.add_field(name="VIP Perks", value="\n".join(f"• {perk}" for perk in self.vip_perks), inline=False)
            embed.add_field(name="__**WARNING**__", value="If you cancel there are __***NO***__ refunds.", inline=False)
            embed.set_footer(text=f"{user.display_name}'s VIP Status", icon_url=user.avatar.url)
        else:
            embed = discord.Embed(
                title="🌟 VIP Membership", 
                description="Upgrade to VIP for exclusive benefits!", 
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Price",
                value=f"{self.vip_price:,} GP/Month",
                inline=False
            )
            embed.add_field(
                name="VIP Perks",
                value="\n".join(f"• {perk}" for perk in self.vip_perks),
                inline=False
            )
            
        return embed

    @commands.command(name="vip")
    async def vip(self, ctx):
        """VIP membership command"""
        await ctx.message.delete()
        is_subscribed = str(ctx.author.id) in self.vip_data
        embed = await self.create_vip_embed(ctx.author, is_subscribed)
        view = VIPView(self, ctx, is_subscribed)
        vipview = await ctx.send(embed=embed, view=view)
        await asyncio.sleep(50)
        await vipview.delete()


    @tasks.loop(hours=8)
    async def check_subscriptions(self):
        """Check and process subscription renewals"""
        current_time = datetime.now()
        
        for user_id, data in list(self.vip_data.items()):
            next_payment = datetime.fromisoformat(data['next_payment'])
            
            if current_time >= next_payment:
                tier_price = self.vip_tiers[data['tier']]['price']

                if await self.process_vip_payment(user_id, tier_price):
                    self.vip_data[user_id]['next_payment'] = (
                        next_payment + timedelta(days=self.vip_tiers[data['tier']]['period'])
                    ).isoformat()
                    self.save_vip_data()
                else:
                    del self.vip_data[user_id]
                    self.save_vip_data()
                    
                    await self.update_user_level(user_id, False)
                    
                    try:
                        user = self.bot.get_user(int(user_id))
                        if user:
                            await user.send("Your VIP subscription has been cancelled due to insufficient funds.")
                    except discord.HTTPException:
                        pass


async def setup(bot):
    await bot.add_cog(VIPSystem(bot))
