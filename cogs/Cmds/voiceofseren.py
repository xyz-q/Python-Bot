import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime, time, timezone, timedelta
import json
import os
import aiohttp
import asyncio


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



    @commands.command(name='addvos')
    @commands.has_permissions(administrator=True)
    async def add_vos_channel(self, ctx):
        """Add current channel to VoS update list"""
        data = self.load_channels()
        if ctx.channel.id not in data['channels']:
            data['channels'].append(ctx.channel.id)
            self.save_channels(data)
            await ctx.send('✅ This channel will now receive Voice of Seren updates!')
        else:
            await ctx.send('This channel is already receiving updates!')

    @commands.command(name='removevos')
    @commands.has_permissions(administrator=True)
    async def remove_vos_channel(self, ctx):
        """Remove current channel from VoS update list"""
        data = self.load_channels()
        if ctx.channel.id in data['channels']:
            data['channels'].remove(ctx.channel.id)
            self.save_channels(data)
            await ctx.send('❌ This channel will no longer receive Voice of Seren updates!')
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
                            current_vos = data['data'][0]  # Get the most recent entry
                            # Parse the UTC timestamp correctly
                            timestamp = datetime.fromisoformat(current_vos['timestamp'].replace('Z', '+00:00'))
                            # Ensure we're in UT
                            timestamp = timestamp.astimezone(timezone.utc) + timedelta(hours=1)
                            return {
                                'timestamp': timestamp,
                                'district1': current_vos['district1'],
                                'district2': current_vos['district2']
                            }
                        else:
                            print("No VoS data found in API response")
                            return None
                    else:
                        print(f"API Error Status: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error in get_vos_data: {e}")
            return None
        
    def create_vos_embed(self, vos_data):
        try:
            current_time = vos_data['timestamp']
            start_time = current_time.strftime("%H:00")
            end_time = current_time.strftime("%H:59")            
            embed = discord.Embed(
                title="<:prif:1336983731952550022> **Last Tracked Voice of Seren** ",
                description=f"Active from `{start_time}` to `{end_time}` UTC",
                color=discord.Color.gold()
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
                
        except Exception as e:
            print(f"Error in create_vos_embed: {e}")
            raise
            
            

            
            


    # @tasks.loop(time=time(minute=52))
    @tasks.loop(minutes=5)
    async def check_vos(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.weirdgloop.org/runescape/vos/history') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'data' in data and len(data['data']) > 0:
                            current_vos = data['data'][0]
                            
                            current_districts = tuple(sorted([
                                current_vos['district1'],
                                current_vos['district2']
                            ]))

                            if self.last_districts is None:
                                self.last_districts = current_districts
                                print(f"Initial VoS districts set to: {current_districts}")
                                return

                            if current_districts != self.last_districts:
                                print(f"VoS changed from {self.last_districts} to {current_districts}")
                                self.last_districts = current_districts
                                
                                vos_data = {
                                    'timestamp': datetime.fromisoformat(current_vos['timestamp'].replace('Z', '+00:00')),
                                    'district1': current_vos['district1'],
                                    'district2': current_vos['district2']
                                }

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
                                                print(f"Successfully sent to channel {channel_id}")
                                            except Exception as e:
                                                print(f"Error sending to channel {channel_id}: {e}")
                                        else:
                                            print(f"Could not find channel {channel_id}")
                                
                                except FileNotFoundError:
                                    print("No channels file found")
                                except json.JSONDecodeError:
                                    print("Error reading channels file")
                                except KeyError:
                                    print("'channels' key not found in JSON file")
                            else:
                                print(f"No change in VoS districts: {current_districts}")
                                
                    else:
                        print(f"Failed to fetch VoS data: HTTP {response.status}")
                        
        except Exception as e:
            print(f"Error in check_vos: {e}")


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
                                
                                await ctx.send(f"Force update complete:\n✅ Sent to {success_count} channels\n❌ Failed in {fail_count} channels")
                            
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
        print("VoS check task initialized...")
        await self.bot.wait_until_ready()


    @add_vos_channel.error
    @remove_vos_channel.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")

async def setup(bot):
    await bot.add_cog(VoSCog(bot))
