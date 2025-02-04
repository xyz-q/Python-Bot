from discord import FFmpegPCMAudio
from discord.ext import commands

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.volume = 1.0

    @commands.command()
    async def volume(self, ctx, volume: float):
        """Change the bot's volume (0.0 to 2.0)"""
        if not 0.0 <= volume <= 2.0:
            await ctx.send("Volume must be between 0.0 and 2.0")
            return
            
        if ctx.voice_client is None:
            await ctx.send("Not connected to a voice channel.")
            return

        ctx.voice_client.source.volume = volume
        self.volume = volume
        await ctx.send(f"Changed volume to {volume*100}%")



async def setup(bot):
    await bot.add_cog(MusicCommands(bot))