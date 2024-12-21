import json
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz
import aiohttp
import discord
from bs4 import BeautifulSoup
import asyncio

class TravellingMerchant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1345
        self.user_preferences = {}
        self.load_preferences()
        self.daily_notification.start()  

    def load_preferences(self):
        try:
            with open('merchant_preferences.json', 'r') as f:
                self.user_preferences = json.load(f)
        except FileNotFoundError:
            self.user_preferences = {}
            self.save_preferences()

    def save_preferences(self):
        with open('merchant_preferences.json', 'w') as f:
            json.dump(self.user_preferences, f)

    @commands.command(name="merch")
    async def toggle_notifications(self, ctx):
        """Toggle daily merchant notifications"""
        user_id = str(ctx.author.id)
        
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
            await ctx.send("❌ Daily merchant notifications disabled.")
        else:
            self.user_preferences[user_id] = True
            await ctx.send("✅ Daily merchant notifications enabled!")
        
        self.save_preferences()


    async def get_merchant_stock(self):
        """Helper function to get the merchant stock"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get('https://runescape.wiki/w/Travelling_Merchant%27s_Shop', headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    

                    inventory_items = soup.find_all('td', class_="inventory-image")[:4]
                    print(f"Found {len(inventory_items)} inventory items")
                    
                    if inventory_items:
                        items = []
             
                        coin_spans = soup.find_all('span', class_="coins")[:4]
                        
                        for item, coin_span in zip(inventory_items, coin_spans):
                     
                            anchor = item.find('a')
                            if anchor and anchor.get('title'):
                                item_name = anchor['title']
                  
                                price = coin_span.text.strip() if coin_span else "Price unknown"
                                items.append((item_name, price))
                                print(f"Added item: {item_name} - {price}")
                        
                        print(f"Final items list: {items}")
                        return items if items else None
                return None

    @commands.command(name="stock")
    async def check_stock_command(self, ctx):
        """Manual command to check merchant stock"""
        try:
            async with ctx.typing():
                items = await self.get_merchant_stock()
                
                if items and len(items) > 0:
                    embed = discord.Embed(
                        title="Travelling Merchant's Stock",
                        description=" ",
                        color=discord.Color.gold(),
                        timestamp = datetime.now(pytz.UTC)
                    )
                    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png") 
                    embed.set_footer(text=datetime.now(pytz.UTC).strftime('%a'))
                    for item_name, price in items:
                        embed.add_field(name=item_name, value=price, inline=False)

                       

                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Unable to fetch the merchant's stock. Please try again later.")
                    
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error in stock command: {e}")


    @tasks.loop(time=time(hour=0, minute=00)) 
    async def daily_notification(self):
        """Send daily notifications to subscribed users"""
        items = await self.get_merchant_stock()
        
        if not items:
            return

        embed = discord.Embed(
            title="Travelling Merchant's Stock",
            description="Today's items:",
            color=discord.Color.gold(),
            timestamp=datetime.now(pytz.UTC)
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png")
        embed.set_footer(text=datetime.now(pytz.UTC).strftime('%a'))
        
        for item_name, price in items:
            embed.add_field(name=item_name, value=price, inline=False)

        # Send to all subscribed users
        for user_id in self.user_preferences:
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    await user.send(embed=embed)
            except Exception as e:
                print(f"Failed to send notification to user {user_id}: {e}")

    @daily_notification.before_loop
    async def before_daily_notification(self):
        """Wait for the bot to be ready before starting the task"""
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.daily_notification.cancel()

    @commands.command(name="merchusers")
    @commands.is_owner()
    async def show_merch_users(self, ctx):
        async with ctx.typing():
            asyncio.sleep(0.5)
        
        """Show all users subscribed to merchant notifications"""
        if not self.user_preferences:
            await ctx.send("No users are currently subscribed to merchant notifications.")
            return

        embed = discord.Embed(
            title="Merchant Notification Subscribers",
            color=discord.Color.red(),
            timestamp=datetime.now(pytz.UTC)
        )

        user_list = []
        for user_id in self.user_preferences:
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_list.append(f"• {user.name} ({user.id})")
            except Exception as e:
                user_list.append(f"• Unknown User ({user_id}) - Could not fetch")


        chunks = [user_list[i:i + 15] for i in range(0, len(user_list), 15)]
        
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                name = f"Subscribers (Part {i}/{len(chunks)})"
            else:
                name = "Subscribers"
            embed.add_field(
                name=name,
                value="\n".join(chunk),
                inline=False
            )

        embed.set_footer(text=f"Total Subscribers: {len(self.user_preferences)}")
        
        await ctx.send(embed=embed)

    @show_merch_users.error
    async def show_merch_users_error(self, ctx, error):
        """Error handler for the merchusers command"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command.")



async def setup(bot):
    await bot.add_cog(TravellingMerchant(bot))
