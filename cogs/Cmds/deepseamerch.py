import json
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta, timezone
import pytz
import aiohttp
import discord
from bs4 import BeautifulSoup
import asyncio
from merchant_stock import stock





class TravellingMerchant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1345
        self.user_preferences = {}
        self.load_preferences()
        self.load_cpreferences()
        self.subscribed_channels = {}  # Changed from self.subscribed.channels
        self.daily_notification.start()  
        self.daily_channel.start()
        self.subscribed_channels = []  # Initialize as empty list
        self.load_subscribed_channels()  
        self.YOUR_USER_ID = 123456789012345678  
        self.item_emojis = {
    "Advanced pulse core": "<:pulsecore:1319913865231863848>",   
    "Anima crystal": "<:anima:1319914262918987827>",   
    "Barrel of bait": "<:bob:1319914681133174787>",   
    "Broken fishing rod": "<:brknrod:1319914596404039700>",   
    "Crystal triskelion": "<:trisk:1319912812939710474>",   
    "Deathtouched dart": "<:dtd:1319912760716427305>",   
    "Distraction & Diversion reset token (daily)": "<:dnddaily:1319914162540777566>",     
    "Distraction & Diversion reset token (monthly)": "<:dndmonthly:1319913049687326783>",   
    "Distraction & Diversion reset token (weekly)": "<:dndweekly:1319913101629456384>",    
    "Dragonkin lamp": "<:dragonkinlamp:1319913393309876284>",   
    "Dungeoneering Wildcard": "<:dungwildcard:1319913320320335943>: 1–3",   
    "Gift for the Reaper": "<:reaper:1319913757522006026>",   
    "Goebie burial charm": "<:mdBC:1319914382716698664>",   
    "Harmonic dust": "<:harmdust:1319912882603032587> 500–1,000",   
    "Horn of honour": "<:hoh:1319913663997542500>",   
    "Large goebie burial charm": "<:lgBC:1319913569139032075>",   
    "Livid plant (Deep Sea Fishing)": "<:livid:1319913820143091793>",   
    "Menaphite gift offering (large)": "<:mgol:1319913203379081246>",   
    "Menaphite gift offering (medium)": "<:mgom:1319914340454895657>",   
    "Menaphite gift offering (small)": "<:mgos:1319914367554424924>",   
    "Message in a bottle (Deep Sea Fishing)": "<:miab:1319913509995151412>",          
    "Sacred clay (Deep Sea Fishing)": "<:sacredclay:1319913989244850228>",   
    "Shattered anima": "<:shatteredanima:1319913925042638888> 500,000–2,000,000",   
    "Silverhawk down": "<:silverhawkdown:1319913701859524618> 50-100",   
    "Slayer VIP Coupon": "<:slayervip:1319914225879224410>",   
    "Small goebie burial charm": "<:smlBC:1319914525364977664>",   
    "Starved ancient effigy": "<:effigy:1319912983815520287>",   
    "Taijitu": "<:taijitu:1319913154763030528> 3–5",   
    "Tangled fishbowl": "<:tangledfish:1319914645057830924>",   
    "Uncharted island map (Deep Sea Fishing)": "<:unchartedmap:1319914742306832416>",         
    "Unfocused damage enhancer": "<:dmgenhan:1319914077702721637>",   
    "Unfocused reward enhancer": "<:rewardenhancer:1319912675282784306>",   
    "Unstable air rune": "<:unsairrune:1319914292891357214> ",   
    "default": "📦"
}

    def load_preferences(self):
        try:
            with open('.json/merchant_preferences.json', 'r') as f:
                self.user_preferences = json.load(f)
        except FileNotFoundError:
            self.user_preferences = {}
            self.save_preferences()

    def save_preferences(self):
        with open('.json/merchant_preferences.json', 'w') as f:
            json.dump(self.user_preferences, f)

    @commands.command(name="merch")
    async def toggle_notifications(self, ctx):
        print("test")
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

    def get_current_stock(self):
        try:
            from merchant_stock import stock
            
            # Get current UTC time
            current_time = datetime.now(timezone.utc)
            current_date = current_time.strftime("%d %B %Y")
            
            # Debug prints
            print(f"Current UTC time: {current_time}")
            print(f"Formatted date: {current_date}")
            print(f"Available stock dates: {list(stock.keys())}")
            
            # Get the stock for the current date
            if current_date in stock:
                return stock[current_date]
            else:
                return None
                
        except Exception as e:
            print(f"Error getting current stock: {str(e)}")
            return None

    @commands.command(name="stock")
    async def check_stock_command(self, ctx):
        """Manual command to check merchant stock"""
        try:
            async with ctx.typing():
                items = await self.get_merchant_stock()

                if items and len(items) > 0:
                    now = datetime.now(pytz.UTC)
                    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    time_until_midnight = next_midnight - now
                    hours, remainder = divmod(time_until_midnight.total_seconds(), 3600)
                    minutes = remainder // 60
                    embed = discord.Embed(
                        title="Travelling Merchant's Stock",
                        description="*Written by* <@110927272210354176>",
                        color=discord.Color.gold(),
                        
                    )
                    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png")
                    embed.set_footer(
                        text=f"Use ,merch to get daily notifications! • Resets in {int(hours)}h {int(minutes)}m"
                    )

                    
                    for item_name, price in items:
                        emoji = self.item_emojis.get(item_name, self.item_emojis["default"])
                        
                        # Skip future date calculation for uncharted island map
                        if item_name == "Uncharted island map (Deep Sea Fishing)":
                            embed.add_field(
                                name=f"{emoji} {item_name}", 
                                value=f"{price} <:goldpoints:1319902464115343473>", 
                                inline=False
                            )
                            continue
                        
                        # Find next occurrence for other items
                        next_date = None
                        today = datetime.now(pytz.UTC).date()
                        
                        for date, daily_items in stock.items():
                            try:
                                stock_date = datetime.strptime(date, '%d %B %Y').date()
                                if stock_date > today and item_name in daily_items:
                                    if next_date is None or stock_date < next_date:
                                        next_date = stock_date
                            except ValueError as e:
                                print(f"Error parsing date {date}: {e}")
                                continue
                        
                        # Calculate days until next appearance and format the message
                        if next_date:
                            days_until = (next_date - today).days
                            next_date_str = f"\nNext appearance: {next_date.strftime('%d %B %Y')}"
                            if days_until == 1:
                                next_date_str += f" (Tomorrow)"
                            else:
                                next_date_str += f" ({days_until} days)"
                        else:
                            next_date_str = "\nNo future appearances found"
    
                        embed.add_field(
                            name=f"{emoji} {item_name}", 
                            value=f"{price} <:goldpoints:1319902464115343473>{next_date_str}", 
                            inline=False
                        )
    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Unable to fetch the merchant's stock. Please try again later.")
                    
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error in stock command: {e}")
    
    
    


    @tasks.loop(time=time(hour=0, minute=0, second=5))
    async def daily_notification(self):
        """Send daily notifications to subscribed users"""
        items = await self.get_merchant_stock()
        
        if not items:
            return
    
        embed = discord.Embed(
            title="Travelling Merchant's Stock",
            description="*Written by* <@110927272210354176>",
            color=discord.Color.gold(),
            timestamp=datetime.now(pytz.UTC)
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png")
        embed.set_footer(text=datetime.now(pytz.UTC).strftime('%a'))
        
        for item_name, price in items:
            emoji = self.item_emojis.get(item_name, self.item_emojis["default"])
            
            # Skip future date calculation for uncharted island map
            if item_name == "Uncharted island map (Deep Sea Fishing)":
                embed.add_field(
                    name=f"{emoji} {item_name}", 
                    value=f"{price} <:goldpoints:1319902464115343473>", 
                    inline=False
                )
                continue
            
            # Find next occurrence for other items
            next_date = None
            today = datetime.now(pytz.UTC).date()
            
            for date, daily_items in stock.items():
                try:
                    stock_date = datetime.strptime(date, '%d %B %Y').date()
                    if stock_date > today and item_name in daily_items:
                        if next_date is None or stock_date < next_date:
                            next_date = stock_date
                except ValueError as e:
                    print(f"Error parsing date {date}: {e}")
                    continue
            
            # Calculate days until next appearance and format the message
            if next_date:
                days_until = (next_date - today).days
                next_date_str = f"\nNext appearance: {next_date.strftime('%d %B %Y')}"
                if days_until == 1:
                    next_date_str += f" (Tomorrow)"
                else:
                    next_date_str += f" ({days_until} days)"
            else:
                next_date_str = "\nNo future appearances found"
    
            embed.add_field(
                name=f"{emoji} {item_name}", 
                value=f"{price} <:goldpoints:1319902464115343473>{next_date_str}", 
                inline=False
            )
    
        # Send to all subscribed users
        for user_id in self.user_preferences:
            try:
                user = await self.bot.fetch_user(int(user_id))
                if user:
                    await user.send(embed=embed)
                    print("sending embed to dms...")
            except Exception as e:
                print(f"Failed to send notification to user {user_id}: {e}")
    
    
    

    @daily_notification.before_loop
    async def before_daily_notification(self):
        """Wait for the bot to be ready before starting the task"""
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.daily_notification.cancel()

    @commands.command(name="merchusers", aliases=['merchers'])
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

    @commands.command(name="listemoji")
    async def list_emojis(self, ctx):
        """Lists all emojis in the current server with their IDs"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server!")
            return

        emoji_list = []
        for emoji in ctx.guild.emojis:
            if emoji.animated:
                emoji_text = f"• {emoji} `<a:{emoji.name}:{emoji.id}>`"
            else:
                emoji_text = f"• {emoji} `<:{emoji.name}:{emoji.id}>`"
            emoji_list.append(emoji_text)

        if not emoji_list:
            await ctx.send("This server has no custom emojis!")
            return

        # Split into chunks of 15 emojis per field (Discord has a limit of 25 fields)
        chunks = [emoji_list[i:i + 15] for i in range(0, len(emoji_list), 15)]
        
        embed = discord.Embed(
            title=f"Emojis in {ctx.guild.name}",
            color=discord.Color.blue()
        )

        # Add fields for each chunk
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                name = f"Emojis (Part {i}/{len(chunks)})"
            else:
                name = "Emojis"
            embed.add_field(
                name=name,
                value="\n".join(chunk),
                inline=False
            )

        embed.set_footer(text=f"Total Emojis: {len(emoji_list)}")
        await ctx.send(embed=embed)



    def load_cpreferences(self):
        try:
            with open('.json/subscribed_channels.json', 'r') as f:
                self.subscribed_channels = json.load(f)
        except FileNotFoundError:
            self.subscribed_channels = {}
            self.save_cpreferences()

    def save_cpreferences(self):
        with open('.json/subscribed_channels.json', 'w') as f:
            json.dump(self.subscribed_channels, f)



    @tasks.loop(time=time(hour=0, minute=0, second=5))  # Using the same format as your daily_notification
    async def daily_channel(self):
        """Send daily notifications to subscribed channels"""
        items = await self.get_merchant_stock()
        
        if not items:
            return

        embed = discord.Embed(
            title="Travelling Merchant's Stock",
            description="*Written by* <@110927272210354176>",
            color=discord.Color.gold(),
            timestamp=datetime.now(pytz.UTC)
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png")
        embed.set_footer(text=datetime.now(pytz.UTC).strftime('%a'))
        
        for item_name, price in items:
            emoji = self.item_emojis.get(item_name, self.item_emojis["default"])
            
            # Skip future date calculation for uncharted island map
            if item_name == "Uncharted island map (Deep Sea Fishing)":
                embed.add_field(
                    name=f"{emoji} {item_name}", 
                    value=f"{price} <:goldpoints:1319902464115343473>", 
                    inline=False
                )
                continue
            
            # Find next occurrence for other items
            next_date = None
            today = datetime.now(pytz.UTC).date()
            
            for date, daily_items in stock.items():
                try:
                    stock_date = datetime.strptime(date, '%d %B %Y').date()
                    if stock_date > today and item_name in daily_items:
                        if next_date is None or stock_date < next_date:
                            next_date = stock_date
                except ValueError as e:
                    print(f"Error parsing date {date}: {e}")
                    continue
            
            # Calculate days until next appearance and format the message
            if next_date:
                days_until = (next_date - today).days
                next_date_str = f"\nNext appearance: {next_date.strftime('%d %B %Y')}"
                if days_until == 1:
                    next_date_str += f" (Tomorrow)"
                else:
                    next_date_str += f" ({days_until} days)"
            else:
                next_date_str = "\nNo future appearances found"

            embed.add_field(
                name=f"{emoji} {item_name}", 
                value=f"{price} <:goldpoints:1319902464115343473>{next_date_str}", 
                inline=False
            )

        # Send to all subscribed channels
        for channel_id in self.subscribed_channels:  # Changed from user_preferences to subscribed_channels
            try:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(embed=embed)
                    
            except Exception as e:
                print(f"Failed to send notification to channel {channel_id}: {e}")

    @commands.command(name="testmerchant")
    @commands.has_permissions(administrator=True)  # Only admins can use this
    async def test_merchant(self, ctx):
        """Test command to manually trigger the merchant notification to all subscribed channels"""
        try:
            # First, confirm to the user that the test is starting
            await ctx.send("Starting merchant notification test...")

            # Get all subscribed channel IDs (you'll need to implement this based on how you store subscribed channels)
            subscribed_channels = self.get_subscribed_channels()  # This method needs to exist in your code
            
            if not subscribed_channels:
                await ctx.send("No subscribed channels found!")
                return

            items = await self.get_merchant_stock()  # Your existing method to get merchant stock
            if not items:
                await ctx.send("No items found in merchant stock.")
                return

            # Create the embed (using your existing embed creation logic)
            embed = discord.Embed(
                title="Travelling Merchant's Stock (TEST)",
                description="*Written by* <@110927272210354176>",
                color=discord.Color.gold(),
                timestamp=datetime.now(pytz.UTC)
            )
            # ... rest of your embed creation code ...

            # Send to all subscribed channels
            success_count = 0
            fail_count = 0
            for channel_id in subscribed_channels:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
                        success_count += 1
                    else:
                        fail_count += 1
                        print(f"Could not find channel with ID: {channel_id}")
                except Exception as e:
                    fail_count += 1
                    print(f"Failed to send to channel {channel_id}: {e}")

            # Report results back to the command user
            await ctx.send(f"Test completed!\n"
                        f"Successfully sent to: {success_count} channels\n"
                        f"Failed to send to: {fail_count} channels")

        except Exception as e:
            await ctx.send(f"An error occurred while testing: {str(e)}")


    def load_subscribed_channels(self):
        """Load subscribed channels from JSON file"""
        try:
            with open('.json/subscribed_channels.json', 'r') as f:
                data = json.load(f)
                self.subscribed_channels = data.get('channels', [])
        except FileNotFoundError:
            self.subscribed_channels = []
            self.save_subscribed_channels()  # Create the file if it doesn't exist
        except json.JSONDecodeError:
            print("Error reading subscribed_channels.json. File might be corrupted.")
            self.subscribed_channels = []

    def save_subscribed_channels(self):
        """Save subscribed channels to JSON file"""
        with open('.json/subscribed_channels.json', 'w') as f:
            json.dump({'channels': self.subscribed_channels}, f, indent=4)

    def get_subscribed_channels(self):
        """Return list of subscribed channel IDs"""
        return self.subscribed_channels

    @commands.command(name="addchannel")
    @commands.is_owner()
    async def subscribe(self, ctx):
        """Subscribe the current channel to merchant notifications"""
        channel_id = ctx.channel.id
        if channel_id not in self.subscribed_channels:
            self.subscribed_channels.append(channel_id)
            self.save_subscribed_channels()
            await ctx.send(f"Channel {ctx.channel.mention} has been subscribed to merchant notifications!")
        else:
            await ctx.send(f"This channel is already subscribed!")

    @commands.command(name="unaddchannel")
    @commands.is_owner()
    async def unsubscribe(self, ctx):
        """Unsubscribe the current channel from merchant notifications"""
        channel_id = ctx.channel.id
        if channel_id in self.subscribed_channels:
            self.subscribed_channels.remove(channel_id)
            self.save_subscribed_channels()
            await ctx.send(f"Channel {ctx.channel.mention} has been unsubscribed from merchant notifications!")
        else:
            await ctx.send(f"This channel is not subscribed!")

    @commands.command(name="listsubscribed")
    @commands.has_permissions(administrator=True)
    async def list_subscribed(self, ctx):
        """List all subscribed channels"""
        if not self.subscribed_channels:
            await ctx.send("No channels are currently subscribed!")
            return
        
        embed = discord.Embed(
            title="Subscribed Channels",
            color=discord.Color.blue()
        )
        
        for channel_id in self.subscribed_channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name=f"#{channel.name}",
                    value=f"ID: {channel_id}\nServer: {channel.guild.name}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Unknown Channel",
                    value=f"ID: {channel_id}\nChannel not found",
                    inline=False
                )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TravellingMerchant(bot))
