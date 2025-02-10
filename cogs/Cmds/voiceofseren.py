import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime, time, timezone, timedelta
import json
import os
import aiohttp
import asyncio

# Add this at the top of your cog
TESTING_MODE = False
class VoSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNELS_FILE = '.json/vos_channels.json'
        self.check_vos.start()
        self.COMBINED_IMAGES = {}  # Initialize the dictionary
        self.load_combined_images()
        self.last_districts = None 
        self.district_emojis = {
            'Amlodd': '<:Amlodd_Clan:1336983757210517555>',  # Replace with your emoji ID
            'Cadarn': '<:Cadarn_Clan:1336983790320488479>',
            'Crwys': '<:Crwys_Clan:1336983771571814460>',
            'Hefin': '<:Hefin_Clan:1336984207242825738>',
            'Iorwerth': '<:Iorwerth_Clan:1336984219879997461>',
            'Ithell': '<:Ithell_Clan:1336984232404451368>',
            'Meilyr': '<:Meilyr_Clan:1336984189844848640>',
            'Trahaearn': '<:Trahaearn_Clan:1336983838945054720>'
        }
    def cog_unload(self):
        self.check_vos.cancel()

    def load_channels(self):
        try:
            with open(self.CHANNELS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"channels": []}

    def save_channels(self, data):
        with open(self.CHANNELS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    async def manage_vos_messages(self, channel):
        """Manage VoS messages to ensure exactly 2 messages exist in the correct order"""
        try:
            info_message = None
            vos_message = None
            
            # Get all messages in channel
            messages = []
            async for message in channel.history(limit=100):
                if message.author == self.bot.user:
                    messages.append(message)
                    
                    # Check for info message
                    if message.embeds and "🎯 Voice of Seren Information Channel" in message.embeds[0].title:
                        info_message = message
                    # Check for VoS update message
                    elif message.embeds and "<:prif:1336983731952550022> Last Tracked Voice of Seren" in message.embeds[0].title:
                        vos_message = message

            # Delete any extra messages from the bot
            for message in messages:
                if message != info_message and message != vos_message:
                    await message.delete()

            return info_message, vos_message
        except Exception as e:
            print(f"Error managing messages: {e}")
            return None, None




    async def clean_channel(self, channel):
        """Clean all user messages and maintain only the two bot messages"""
        try:
            # Delete all user messages
            async for message in channel.history(limit=100):
                if message.author != self.bot.user:
                    await message.delete()
                elif message.author == self.bot.user:
                    if message.embeds:
                        # Keep only messages with specific titles
                        if not (("🎯 Voice of Seren Information Channel" in message.embeds[0].title) or 
                            ("<:prif:1336983731952550022> Last Tracked Voice of Seren" in message.embeds[0].title)):
                            await message.delete()
        except Exception as e:
            print(f"Error cleaning channel: {e}")

    @commands.command(name='addvos')
    @commands.has_permissions(administrator=True)
    async def add_vos_channel(self, ctx):
        """Add current channel to VoS update list"""
        try:
            data = self.load_channels()
            if ctx.channel.id not in data['channels']:
                # Add channel to update list
                data['channels'].append(ctx.channel.id)
                self.save_channels(data)
                
                success_message = await ctx.send('<:add:1328511998647861390> This channel will now receive Voice of Seren updates!')
                await asyncio.sleep(5)
                await success_message.delete()
            else:
                temp_message = await ctx.send('This channel is already receiving updates!')
                await asyncio.sleep(5)
                await temp_message.delete()

        except Exception as e:
            error_message = await ctx.send(f"An error occurred: {str(e)}")
            await asyncio.sleep(5)
            await error_message.delete()


    @commands.command(name='removevos')
    @commands.has_permissions(administrator=True)
    async def remove_vos_channel(self, ctx):
        """Remove current channel from VoS update list"""
        data = self.load_channels()
        if ctx.channel.id in data['channels']:
            data['channels'].remove(ctx.channel.id)
            self.save_channels(data)
            await ctx.send('<:remove:1328511957208268800> This channel will no longer receive Voice of Seren updates!')
        else:
            await ctx.send('This channel was not receiving updates!')

    @commands.command()
    async def vos(self, ctx):
        try:
            status_message = await ctx.send("Fetching Voice of Seren data...")
            
            vos_data = await self.get_vos_data()
            if not vos_data:
                await status_message.edit(content="Unable to fetch Voice of Seren data.")
                return
                
            embed, file = self.create_vos_embed(vos_data)
            await status_message.delete()
            
            if file:
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            print(f"Error in vos command: {e}")
            await ctx.send(f"An error occurred while processing the command: {str(e)}")

            
            


    def load_combined_images(self):
        vos_dir = "data/vos_combinations"
        for filename in os.listdir(vos_dir):
            if filename.endswith(".png"):
                districts = filename[:-4].split('_')
                key = tuple(sorted(districts))
                self.COMBINED_IMAGES[key] = os.path.join(vos_dir, filename)

    async def get_vos_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.weirdgloop.org/runescape/vos/history') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'data' in data and len(data['data']) > 0:
                            current_vos = data['data'][0]
                            timestamp = datetime.fromisoformat(current_vos['timestamp'].replace('Z', '+00:00'))
                            timestamp = timestamp.astimezone(timezone.utc)
                            
                            # Get current UTC time
                            current_time = datetime.now(timezone.utc)
                            
                            vos_data = {
                                'timestamp': timestamp,
                                'district1': current_vos['district1'],
                                'district2': current_vos['district2'],
                                'current_hour': current_time.hour,
                                'data_hour': timestamp.hour
                            }

                            # Test condition to force stale data
                            if TESTING_MODE:
                                vos_data['is_stale'] = True
                                vos_data['current_hour'] = (timestamp.hour + 1) % 24  # Simulate next hour
                            else:
                                # Normal check
                                if current_time.hour > timestamp.hour or \
                                (current_time.hour == 0 and timestamp.hour == 23):
                                    vos_data['is_stale'] = True
                                else:
                                    vos_data['is_stale'] = False

                            return vos_data

                        return None
        except Exception as e:
            print(f"Error fetching VoS data: {e}")
            return None
        
    def create_vos_embed(self, vos_data):
        if not vos_data:
            return discord.Embed(
                title="Error",
                description="Unable to fetch Voice of Seren data",
                color=discord.Color.red()
            ), None

        if vos_data.get('is_stale', False):
            embed = discord.Embed(
                title="<:prif:1336983731952550022> **Voice of Seren**",
                description=f"<:remove:1328511957208268800> The Voice of Seren is out of date\n\n"
                        f"Last known data is from `{vos_data['data_hour']:02d}:00` UTC\n"
                        f"Current hour is `{vos_data['current_hour']:02d}:00` UTC\n\n"
                        f"Last known districts were:\n"
                        f"• `{vos_data['district1']}`\n"
                        f"• `{vos_data['district2']}`",
                color=discord.Color.orange()
            )
            embed.set_footer(text="• Waiting for new Voice of Seren data •")
            return embed, None
        
        # Regular embed for current data
        current_time = vos_data['timestamp']
        start_time = current_time.strftime("%H:00")
        end_time = current_time.strftime("%H:59")
        
        embed = discord.Embed(
            title="<:prif:1336983731952550022> **Voice of Seren**",
            description=f"Active from `{start_time}` to `{end_time}` UTC",
            color=discord.Color.teal()
        )

        key = tuple(sorted([vos_data['district1'], vos_data['district2']]))
        if key in self.COMBINED_IMAGES:
            file = discord.File(self.COMBINED_IMAGES[key], filename="districts.png")
            embed.set_thumbnail(url="attachment://districts.png")
            
            # Get emojis for each district
            emoji1 = self.district_emojis.get(vos_data['district1'], '')
            emoji2 = self.district_emojis.get(vos_data['district2'], '')
            
            embed.add_field(
                name=f"{emoji1} __`{vos_data['district1']}`__\n    __`District`__",
                value="",
                inline=True
            )

            embed.add_field(
                name=f"{emoji2} __`{vos_data['district2']}`__\n   __`District`__",
                value="",
                inline=True
            )
            
            embed.set_footer(text="• Data provided by WeirdGloop API •")
            return embed, file
        
        return embed, None

            
            

            
            


    # @tasks.loop(time=time(minute=52))
    @tasks.loop(minutes=3)
    async def check_vos(self):
        try:
            vos_data = await self.get_vos_data()
            if not vos_data:
                return

            current_districts = tuple(sorted([
                vos_data['district1'],
                vos_data['district2']
            ]))

            data = self.load_channels()
            for channel_id in data['channels']:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        # Clean channel first
                        await self.clean_channel(channel)
                        
                        # Check for existing messages
                        info_message, vos_message = await self.manage_vos_messages(channel)
                        
                        # Create info message if it doesn't exist
                        if not info_message:
                            setup_embed = discord.Embed(
                                title="🎯 Voice of Seren Information Channel",
                                description="This channel will automatically update with the latest Voice of Seren information.\n\nUpdates occur every hour.\n\nThe Voice of Seren is a blessing effect in Prifddinas that moves between clan districts every hour.",
                                color=discord.Color.teal()
                            )
                            await channel.send(embed=setup_embed)
                        
                        # Update VoS message if districts changed OR if there's no VoS message
                        if (self.last_districts is None or 
                            current_districts != self.last_districts or 
                            vos_message is None):
                            
                            # Create new embed and file
                            new_embed, new_file = self.create_vos_embed(vos_data)
                            
                            # Delete old VoS message if it exists
                            if vos_message:
                                await vos_message.delete()
                            
                            # Send new VoS message
                            await channel.send(file=new_file, embed=new_embed)  # Fixed here: using new_embed instead of embed

                    except Exception as e:
                        print(f"Error updating channel {channel_id}: {e}")
                else:
                    print(f"Could not find channel {channel_id}")
            
            self.last_districts = current_districts

        except Exception as e:
            print(f"Error in check_vos: {e}")

    @commands.command()
    @commands.is_owner()  # Only bot owner can use this
    async def test_vos(self, ctx):
        global TESTING_MODE
        TESTING_MODE = not TESTING_MODE
        await ctx.send(f"Testing mode is now {'enabled' if TESTING_MODE else 'disabled'}")



# Add an event listener for new messages
    @commands.Cog.listener()
    async def on_message(self, message):
        """Delete non-bot messages immediately in VoS channels"""
        try:
            # Check if the message is in a VoS channel
            data = self.load_channels()
            if message.channel.id in data['channels']:
                # If it's not a bot message, delete it
                if message.author != self.bot.user:
                    await message.delete()
        except Exception as e:
            print(f"Error in on_message: {e}")
                  
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcevos(self, ctx):
        """Force send VoS update to all channels"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.weirdgloop.org/runescape/vos/history') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'data' in data and len(data['data']) > 0:
                            current_vos = data['data'][0]
                            
                            vos_data = {
                                'timestamp': datetime.fromisoformat(current_vos['timestamp'].replace('Z', '+00:00')),
                                'district1': current_vos['district1'],
                                'district2': current_vos['district2']
                            }
                            
                            success_count = 0
                            fail_count = 0
                            
                            try:
                                with open(self.CHANNELS_FILE, 'r') as f:
                                    data = json.load(f)
                                    channels = data['channels']
                                
                                for channel_id in channels:
                                    channel = self.bot.get_channel(channel_id)
                                    if channel:
                                        try:
                                            # Create new embed and file for each channel
                                            embed, file = self.create_vos_embed(vos_data)
                                            if file:
                                                await channel.send(file=file, embed=embed)
                                            else:
                                                await channel.send(embed=embed)
                                            success_count += 1
                                            print(f"Successfully sent to channel {channel_id}")
                                        except Exception as e:
                                            fail_count += 1
                                            print(f"Error sending to channel {channel_id}: {e}")
                                    else:
                                        fail_count += 1
                                        print(f"Could not find channel {channel_id}")
                                
                                await ctx.send(f"Force update complete:\n<:add:1328511998647861390> Sent to {success_count} channels\n<:remove:1328511957208268800> Failed in {fail_count} channels")
                            
                            except FileNotFoundError:
                                await ctx.send("No channels file found")
                            except json.JSONDecodeError:
                                await ctx.send("Error reading channels file")
                            except KeyError:
                                await ctx.send("'channels' key not found in JSON file")
                    else:
                        await ctx.send(f"Failed to fetch VoS data: HTTP {response.status}")
        except Exception as e:
            await ctx.send(f"Error during force update: {e}")


    @check_vos.before_loop
    async def before_check_vos(self):

        await self.bot.wait_until_ready()


    @add_vos_channel.error
    @remove_vos_channel.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("<:remove:1328511957208268800> You need administrator permissions to use this command!")

async def setup(bot):
    await bot.add_cog(VoSCog(bot))