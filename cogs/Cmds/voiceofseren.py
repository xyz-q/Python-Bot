import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import json
import os
import aiohttp
import asyncio


STATE_FILE = ".json/vos_state.json"


class VoSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNELS_FILE = '.json/vos_channels.json'
        self.COMBINED_IMAGES = {}
        self.load_combined_images()
        self.channel_state = self._load_state()
        self.district_emojis = {
            'Amlodd':    '<:Amlodd_Clan:1336983757210517555>',
            'Cadarn':    '<:Cadarn_Clan:1336983790320488479>',
            'Crwys':     '<:Crwys_Clan:1336983771571814460>',
            'Hefin':     '<:Hefin_Clan:1336984207242825738>',
            'Iorwerth':  '<:Iorwerth_Clan:1336984219879997461>',
            'Ithell':    '<:Ithell_Clan:1336984232404451368>',
            'Meilyr':    '<:Meilyr_Clan:1336984189844848640>',
            'Trahaearn': '<:Trahaearn_Clan:1336983838945054720>'
        }
        self.check_vos.start()

    def _load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                raw = json.load(f)
                # JSON keys are strings, convert back to int and lists to tuples
                return {int(k): {"districts": tuple(v["districts"]), "is_stale": v["is_stale"]} for k, v in raw.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_state(self):
        os.makedirs(".json", exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({str(k): {"districts": list(v["districts"]), "is_stale": v["is_stale"]} for k, v in self.channel_state.items()}, f)

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

    def load_combined_images(self):
        vos_dir = "data/vos_combinations"
        for filename in os.listdir(vos_dir):
            if filename.endswith(".png"):
                districts = filename[:-4].split('_')
                self.COMBINED_IMAGES[tuple(sorted(districts))] = os.path.join(vos_dir, filename)

    async def get_vos_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.weirdgloop.org/runescape/vos') as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    if not data or 'timestamp' not in data:
                        return None
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')).astimezone(timezone.utc)
                    current_time = datetime.now(timezone.utc)
                    is_stale = current_time.hour != timestamp.hour or current_time.date() != timestamp.date()
                    return {
                        'timestamp': timestamp,
                        'district1': data['district1'],
                        'district2': data['district2'],
                        'is_stale': is_stale,
                        'data_hour': timestamp.hour,
                        'current_hour': current_time.hour,
                    }
        except Exception as e:
            print(f"Error fetching VoS data: {e}")
            return None

    def create_vos_embed(self, vos_data):
        if vos_data.get('is_stale'):
            embed = discord.Embed(
                title="<:prif:1336983731952550022> **Voice of Seren**",
                description=(
                    f"<:remove:1328511957208268800> The Voice of Seren is out of date\n\n"
                    f"Last known data is from `{vos_data['data_hour']:02d}:00` UTC\n"
                    f"Current hour is `{vos_data['current_hour']:02d}:00` UTC\n\n"
                    f"Last known districts were:\n"
                    f"• `{vos_data['district1']}`\n"
                    f"• `{vos_data['district2']}`"
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="• The data refreshes every 5 minutes •")
            return embed, None

        start_time = vos_data['timestamp'].strftime("%H:00")
        end_time = vos_data['timestamp'].strftime("%H:59")
        embed = discord.Embed(
            title="<:prif:1336983731952550022> **Voice of Seren**",
            description=f"Active from `{start_time}` to `{end_time}` UTC",
            color=discord.Color.teal()
        )
        key = tuple(sorted([vos_data['district1'], vos_data['district2']]))
        file = None
        if key in self.COMBINED_IMAGES:
            file = discord.File(self.COMBINED_IMAGES[key], filename="districts.png")
            embed.set_thumbnail(url="attachment://districts.png")
        emoji1 = self.district_emojis.get(vos_data['district1'], '')
        emoji2 = self.district_emojis.get(vos_data['district2'], '')
        embed.add_field(name=f"{emoji1} __`{vos_data['district1']}`__\n    __`District`__", value="", inline=True)
        embed.add_field(name=f"{emoji2} __`{vos_data['district2']}`__\n   __`District`__", value="", inline=True)
        embed.set_footer(text="• Data provided by WeirdGloop API •")
        return embed, file

    async def _send_vos(self, channel, vos_data):
        """Delete old VoS message and send a fresh one."""
        messages = [msg async for msg in channel.history(limit=100) if msg.author == self.bot.user]
        for msg in messages:
            if msg.embeds and "Voice of Seren" in msg.embeds[0].title:
                try:
                    await msg.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

        embed, file = self.create_vos_embed(vos_data)
        msg = await channel.send(file=file, embed=embed)

        # Publish if it's a news channel
        if isinstance(channel, discord.TextChannel) and channel.is_news():
            try:
                await msg.publish()
            except (discord.Forbidden, discord.HTTPException):
                pass

    @tasks.loop(seconds=300)
    async def check_vos(self):
        try:
            vos_data = await self.get_vos_data()
            if not vos_data:
                print("❌ No VoS data received")
                return

            current_districts = tuple(sorted([vos_data['district1'], vos_data['district2']]))
            is_stale = vos_data['is_stale']

            for channel_id in self.load_channels()['channels']:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue
                try:
                    prev = self.channel_state.get(channel_id)

                    if prev is None:
                        # First run — always send
                        await self._send_vos(channel, vos_data)
                        self.channel_state[channel_id] = {"districts": current_districts, "is_stale": is_stale}
                        self._save_state()
                        continue

                    prev_districts = prev["districts"]
                    prev_stale = prev["is_stale"]

                    if not is_stale and current_districts != prev_districts:
                        await self._send_vos(channel, vos_data)
                        self.channel_state[channel_id] = {"districts": current_districts, "is_stale": False}
                        self._save_state()

                    elif not prev_stale and is_stale:
                        await self._send_vos(channel, vos_data)
                        self.channel_state[channel_id] = {"districts": current_districts, "is_stale": True}
                        self._save_state()

                    elif prev_stale and is_stale:
                        pass

                    elif prev_stale and not is_stale:
                        await self._send_vos(channel, vos_data)
                        self.channel_state[channel_id] = {"districts": current_districts, "is_stale": False}
                        self._save_state()

                except Exception as e:
                    print(f"❌ Error updating channel {channel_id}: {e}")

        except Exception as e:
            print(f"❌ Error in check_vos: {e}")

    @check_vos.before_loop
    async def before_check_vos(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        data = self.load_channels()
        if message.channel.id in data['channels']:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

    @commands.command(name='addvos')
    @commands.has_permissions(administrator=True)
    async def add_vos_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        data = self.load_channels()
        if channel.id not in data['channels']:
            data['channels'].append(channel.id)
            self.save_channels(data)
            msg = await ctx.send(f'<:add:1328511998647861390> {channel.mention} will now receive Voice of Seren updates!')
        else:
            msg = await ctx.send('This channel is already receiving updates!')
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command(name='removevos')
    @commands.has_permissions(administrator=True)
    async def remove_vos_channel(self, ctx):
        data = self.load_channels()
        if ctx.channel.id in data['channels']:
            data['channels'].remove(ctx.channel.id)
            self.save_channels(data)
            self.channel_state.pop(ctx.channel.id, None)
            self._save_state()
            await ctx.send('<:remove:1328511957208268800> This channel will no longer receive Voice of Seren updates!')
        else:
            await ctx.send('This channel was not receiving updates!')

    @commands.command()
    async def vos(self, ctx):
        vos_data = await self.get_vos_data()
        if not vos_data:
            await ctx.send("Unable to fetch Voice of Seren data.")
            return
        embed, file = self.create_vos_embed(vos_data)
        await ctx.send(file=file, embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcevos(self, ctx):
        vos_data = await self.get_vos_data()
        if not vos_data:
            await ctx.send("Failed to fetch VoS data.")
            return
        success, fail = 0, 0
        for channel_id in self.load_channels()['channels']:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await self._send_vos(channel, vos_data)
                    self.channel_state[channel_id] = {
                        "districts": tuple(sorted([vos_data['district1'], vos_data['district2']])),
                        "is_stale": vos_data['is_stale']
                    }
                    self._save_state()
                    success += 1
                except Exception as e:
                    print(f"forcevos error in {channel_id}: {e}")
                    fail += 1
            else:
                fail += 1
        await ctx.send(f"<:add:1328511998647861390> {success} sent  <:remove:1328511957208268800> {fail} failed")

    @add_vos_channel.error
    @remove_vos_channel.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("<:remove:1328511957208268800> You need administrator permissions to use this command!")


async def setup(bot):
    await bot.add_cog(VoSCog(bot))
