import discord
from discord.ext import commands, tasks
import aiohttp
import sys
import os
import asyncio
import json
from difflib import get_close_matches

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from elydata import data

class ElyNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_dictionary = data
        self.price_alerts = {}
        self.alerts_file = 'alerts.json'
        self.load_alerts()  # Load saved alerts when bot starts
        self.check_prices.start()

        self.item_aliases = {
            "black xmas": "black christmas scythe",
            "black xmas scythe": "black christmas scythe",         
            "2a": "second age",
            "3a": "third age",
             "3a dye": "third age dye",
            "3a top": "third age platebody",
            "3a bottoms": "third age platelegs",
            "walks": "walk",
            "scythes": "scythe",
            "disk": "disk of returning",
            "xmas": "christmas",
            "bph": "black partyhat",
            "black": "black partyhat",
            "red": "red partyhat",
            "white": "white partyhat",
            "blue": "blue partyhat",
            "green": "green partyhat",
            "purple": "purple partyhat",
            "yellow": "yellow partyhat",
            "bsh": "black santa hat",
            "rsh": "red santa hat",
            "hween": "halloween mask",
            "xmas": "christmas",
            "hsr": "signet ring",
            "osh": "orlando",            
            "bcs": "black christmas scythe",            
            "phats": "partyhat",
            "phat set": "partyhat",
            "phat set": "partyhat",
            "phat": "partyhat",
            "hween set": "halloween mask",
            "hweens": "halloween mask",
            "santas": "santa hat",
            "blue hween": "blue halloween mask",
            "green hween": "green halloween mask",
            "red hween": "red halloween mask",
            "purple hween": "purple halloween mask",
            "orange hween": "orange halloween mask",
            "orange": "orange halloween mask",
            "taggas": "tagga's",
            "fyre": "sana's fyrtorch",
            "hypno": "skeka's hypnowand",                     
        }

    def load_alerts(self):
        """Load alerts from JSON file"""
        print("\nLoading saved alerts...")
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    # Convert string keys back to integers
                    data = json.load(f)
                    self.price_alerts = {int(k): v for k, v in data.items()}
                print(f"Loaded {len(self.price_alerts)} users' alerts")
            else:
                print("No saved alerts found")
        except Exception as e:
            print(f"Error loading alerts: {e}")
            self.price_alerts = {}

    def save_alerts(self):
        """Save alerts to JSON file"""
        print("\nSaving alerts...")
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump(self.price_alerts, f, indent=4)
            print("Alerts saved successfully")
        except Exception as e:
            print(f"Error saving alerts: {e}")


    def process_item_name(self, item_name: str) -> str:
        """Process item name and check for aliases"""
        print(f"Processing item name: {item_name}")
        
        item_lower = item_name.lower()
        
        # Check aliases first
        if item_lower in self.item_aliases:
            return self.item_aliases[item_lower]
            
        all_item_names = [item['value'].lower() for item in self.item_dictionary]
        
        if item_lower in all_item_names:
            return item_lower
            
        complete_matches = get_close_matches(item_lower, all_item_names, n=1, cutoff=0.7)
        if complete_matches:
            return complete_matches[0]
            
        words = item_lower.split()
        final_words = []
        
        for word in words:
            if word in all_item_names:
                final_words.append(word)
                continue
                
            word_matches = get_close_matches(word, all_item_names, n=1, cutoff=0.7)
            if word_matches:
                final_words.append(word_matches[0])
            else:
                final_words.append(word)
        
        result = " ".join(final_words)
        print(f"Processed search term: {result}")
        return result

    def convert_price_string(self, price_str: str) -> int:
        """Convert price string (e.g., "100k", "1.5m") to number"""
        price_str = price_str.lower().strip()
        multiplier = 1

        if price_str.endswith('k'):
            multiplier = 1000
            price_str = price_str[:-1]
        elif price_str.endswith('m'):
            multiplier = 1000000
            price_str = price_str[:-1]
        elif price_str.endswith('b'):
            multiplier = 1000000000
            price_str = price_str[:-1]

        try:
            return int(float(price_str) * multiplier)
        except ValueError:
            raise ValueError("Invalid price format")

    @tasks.loop(minutes=15)
    async def check_prices(self):
        print("\nChecking prices for alerts...")
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Opera GX";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for user_id, alerts in self.price_alerts.items():
            user = self.bot.get_user(user_id)
            if not user:
                print(f"Could not find user {user_id}")
                continue

            for alert in alerts[:]:
                item_id, target_price, item_name, direction = alert
                print(f"Checking {item_name} for user {user.name}")
                
                try:
                    url = f"https://www.ely.gg/chart/{item_id}/prices"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data['items']:
                                    current_price = data['items'][-1]['price']
                                    print(f"{item_name} current price: {current_price}, target: {target_price}, direction: {direction}")
                                    
                                    condition_met = (direction == 'h' and current_price >= target_price) or \
                                                  (direction == 'l' and current_price <= target_price)
                                    
                                    if condition_met:
                                        direction_text = "risen above" if direction == 'h' else "dropped below"
                                        embed = discord.Embed(
                                            title="Price Alert!",
                                            description=f"{item_name} has {direction_text} your target price!",
                                            color=discord.Color.green()
                                        )
                                        embed.add_field(name="Current Price", value=f"{current_price:,} gp")
                                        embed.add_field(name="Your Target", value=f"{target_price:,} gp")
                                        
                                        try:
                                            await user.send(embed=embed)
                                            self.price_alerts[user_id].remove(alert)
                                            self.save_alerts()  # Save after alert triggers
                                            print(f"Alert sent to {user.name} for {item_name}")
                                        except discord.Forbidden:
                                            print(f"Could not send DM to {user.name}")
                
                except Exception as e:
                    print(f"Error checking price for {item_name}: {e}")
                
                await asyncio.sleep(0.5)  # Prevent rate limiting

    @check_prices.before_loop
    async def before_check_prices(self):
        await self.bot.wait_until_ready()

    @commands.command(name='notify', aliases=['alert', 'setalert'])
    async def add_alert(self, ctx, *, text: str = None):
        print(f"\nNotify command received from {ctx.author}: {text}")
        
        if text is None:
            await ctx.send("Please use: ,notify [item name] [price] [h/l]\nExample: ,notify bcs 85m h")
            return

        try:
            *item_parts, price_str, direction = text.split()
            item_name = ' '.join(item_parts)
            
            if direction.lower() not in ['h', 'l']:
                await ctx.send("Direction must be 'h' for higher or 'l' for lower")
                return
                
        except ValueError:
            await ctx.send("Please use: ,notify [item name] [price] [h/l]\nExample: ,notify bcs 85m h")
            return

        processed_name = self.process_item_name(item_name)
        print(f"Processed name: {processed_name}")

        try:
            target_price = self.convert_price_string(price_str)
        except ValueError:
            await ctx.send("Invalid price format. Examples: 100k, 1.5m, 2b")
            return

        matches = []
        for item in self.item_dictionary:
            if processed_name in item['value'].lower():
                matches.append(item)

        if not matches:
            await ctx.send(f"Could not find item: {item_name}")
            return

        item = matches[0]
        alert_data = (item['id'], target_price, item['value'], direction.lower())

        if ctx.author.id not in self.price_alerts:
            self.price_alerts[ctx.author.id] = []
        
        if alert_data not in self.price_alerts[ctx.author.id]:
            self.price_alerts[ctx.author.id].append(alert_data)
            self.save_alerts()  # Save after adding alert
            direction_text = "rises above" if direction.lower() == 'h' else "drops below"
            await ctx.send(f"Alert set! You'll be notified when {item['value']} {direction_text} {target_price:,} gp")
            print(f"Alert set for {ctx.author}: {item['value']} at {target_price:,} gp ({direction_text})")
        else:
            await ctx.send("You already have an alert set for this item!")

    @commands.command(name='myalerts')
    async def list_alerts(self, ctx):
        print(f"\nListing alerts for {ctx.author}")
        
        if ctx.author.id not in self.price_alerts or not self.price_alerts[ctx.author.id]:
            await ctx.send("You don't have any active alerts!")
            return

        embed = discord.Embed(
            title="Your Price Alerts",
            color=discord.Color.gold()
        )

        for item_id, target_price, item_name, direction in self.price_alerts[ctx.author.id]:
            direction_text = ">" if direction == 'h' else "<"
            embed.add_field(
                name=item_name,
                value=f"Target: {direction_text} {target_price:,} gp",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='removealert')
    async def remove_alert(self, ctx, *, item_name: str):
        print(f"\nRemoving alert for {ctx.author}: {item_name}")
        
        if ctx.author.id not in self.price_alerts:
            await ctx.send("You don't have any active alerts!")
            return

        processed_name = self.process_item_name(item_name)
        alerts = self.price_alerts[ctx.author.id]
        
        for alert in alerts[:]:
            if processed_name in alert[2].lower():
                self.price_alerts[ctx.author.id].remove(alert)
                self.save_alerts()  # Save after removing alert
                await ctx.send(f"Alert removed for {alert[2]}")
                print(f"Alert removed for {ctx.author}: {alert[2]}")
                return

        await ctx.send(f"No alert found for {item_name}")

    @commands.command(name='alerts')
    @commands.is_owner()  # This makes the command only usable by the bot owner
    async def all_alerts(self, ctx):
        print("\nListing all alerts for all users")
        
        if not self.price_alerts:
            await ctx.send("There are no active alerts!")
            return

        embeds = []
        current_embed = discord.Embed(
            title="All Active Alerts",
            color=discord.Color.gold()
        )
        field_count = 0

        for user_id, alerts in self.price_alerts.items():
            user = self.bot.get_user(user_id)
            if not user:
                username = f"Unknown User ({user_id})"
            else:
                username = user.name

            if not alerts:
                continue

            # Create field for each user's alerts
            alert_text = ""
            for item_id, target_price, item_name, direction in alerts:
                direction_text = ">" if direction == 'h' else "<"
                alert_text += f"{item_name}: {direction_text} {target_price:,} gp\n"

            # If this embed is full (25 fields), create a new one
            if field_count >= 25:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="All Active Alerts (Continued)",
                    color=discord.Color.gold()
                )
                field_count = 0

            current_embed.add_field(
                name=f"Alerts for {username}",
                value=alert_text or "No alerts",
                inline=False
            )
            field_count += 1

        # Add the last embed if it has any fields
        if field_count > 0:
            embeds.append(current_embed)

        # Add total count to first embed's description
        total_alerts = sum(len(alerts) for alerts in self.price_alerts.values())
        total_users = len(self.price_alerts)
        embeds[0].description = f"Total Alerts: {total_alerts}\nTotal Users: {total_users}"

        # Send all embeds
        for embed in embeds:
            await ctx.send(embed=embed)



    def cog_unload(self):
        """Save alerts when cog is unloaded"""
        self.check_prices.cancel()
        self.save_alerts()

async def setup(bot):
    print("\nSetting up ElyNotify cog")
    await bot.add_cog(ElyNotify(bot))
