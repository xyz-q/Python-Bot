import discord
from discord.ext import commands, tasks
import asyncio

class VoiceTimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_state_check.start()
        self.empty_voice_channels = {}

    def cog_unload(self):
        self.voice_state_check.cancel()

    @tasks.loop(seconds=60)  
    async def voice_state_check(self):
        for guild in self.bot.guilds:
            if guild.voice_client is not None:
                voice_channel = guild.voice_client.channel
                if len(voice_channel.members) == 1 and self.bot.user in voice_channel.members:
                    if voice_channel.id in self.empty_voice_channels:
                        time_elapsed = asyncio.get_event_loop().time() - self.empty_voice_channels[voice_channel.id]
                        if time_elapsed >= 300: 
                            await guild.voice_client.disconnect()
                            await print("Bot has left the channel due to inactivity.")
                            del self.empty_voice_channels[voice_channel.id]
                    else:
                        self.empty_voice_channels[voice_channel.id] = asyncio.get_event_loop().time()
                else:
                    if voice_channel.id in self.empty_voice_channels:
                        del self.empty_voice_channels[voice_channel.id]

    @voice_state_check.before_loop
    async def before_voice_state_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user:
            return

        if before.channel is not None and self.bot.user in before.channel.members:
            if len(before.channel.members) == 1:
                self.empty_voice_channels[before.channel.id] = asyncio.get_event_loop().time()
            else:
                if before.channel.id in self.empty_voice_channels:
                    del self.empty_voice_channels[before.channel.id]


async def setup(bot):
    await bot.add_cog(VoiceTimeout(bot))
