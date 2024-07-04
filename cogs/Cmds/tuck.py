import discord
from discord.ext import commands

class Tuck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = 1082555334838734879
        self.user_ids = [1223399500517867561, 781587562736910396, 110927272210354176, 611026142270324737]

    @commands.command(name='tuck', aliases=['sleep'])
    async def move_users(self, ctx):
        target_channel = self.bot.get_channel(self.target_channel_id)

        if not isinstance(target_channel, discord.VoiceChannel):
            await ctx.send(f"Channel ID {self.target_channel_id} is not a valid voice channel.")
            return

        for user_id in self.user_ids:
            user = ctx.guild.get_member(user_id)
            if user and user.voice and user.voice.channel:
                await user.move_to(target_channel)
        await ctx.send("tucked in goodnight <3")
            
async def setup(bot):
    await bot.add_cog(Tuck(bot))
