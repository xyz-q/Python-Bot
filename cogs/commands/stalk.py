import discord
from discord.ext import commands, tasks


class Stalk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.followed_user = None
        self.follow_user.start()

    @commands.command(name='stalk', help='Stalk a user in their current voice channel.')
    async def stalk(self, ctx, member: discord.Member):
        # Check if the bot is already in a voice channel
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            voice_channel = voice_client.channel
        else:
            voice_channel = None

        # Connect/move to the voice channel if available
        if member.voice and member.voice.channel:
            voice_channel = member.voice.channel
            try:
                if not voice_client:
                    await voice_channel.connect()
                else:
                    await voice_client.move_to(voice_channel)
            except discord.ClientException:
                await ctx.send("Failed to connect to the voice channel.")
                return
        else:
            await ctx.send(f"{member.display_name} is not in a voice channel, or the bot isn't in a voice channel. Starting the loop anyway...", delete_after=1)
            print(f"Started stalking {member.display_name} even though they are not in a voice channel.")

        self.followed_user = member
        await ctx.send(f"Now stalking {member.display_name} in {voice_channel.name}.", delete_after=1)
        print(f"\033[30mNow stalking\033[0m \033[91m{member.display_name}\033[0m \033[30min\033[0m \033[91m{voice_channel.name}\033[0m.")
        await ctx.message.delete(delay=1)

    @commands.command(name='stopstalk', help='Stop stalking the currently stalked user.')
    async def stopstalk(self, ctx):
        if self.followed_user:
            voice_client = ctx.guild.voice_client
            if voice_client:
                await voice_client.disconnect()
            await ctx.send(f"Stopped stalking {self.followed_user.display_name}.")
            self.followed_user = None
        else:
            await ctx.send("The bot is not currently stalking anyone.")

    @tasks.loop(seconds=4)
    async def follow_user(self):
        if self.followed_user and self.followed_user.voice:
            guild = self.followed_user.guild
            voice_channels = guild.voice_channels

            # Check if the followed user is still in a voice channel
            if self.followed_user.voice.channel is None:
                print(f"{self.followed_user.display_name} has left the voice channel. Stopping the loop.")
                await self.follow_user.stop()  # Stop the loop if the user has left the voice channel
                return

            # Check all voice channels for the user
            for voice_channel in voice_channels:
                if self.followed_user in voice_channel.members:
                    # User found in this channel, join it
                    voice_client = guild.voice_client

                    if voice_client is None:
                        try:
                            # Connect to the user's voice channel
                            await voice_channel.connect(timeout=5)
                        except discord.ClientException:
                            pass  # Failed to connect, may already be connected elsewhere or missing permissions
                    else:
                        if voice_client.is_connected() and voice_client.channel:
                            # Check if the bot is already in the user's channel
                            if voice_client.channel != voice_channel:
                                try:
                                    # Move the bot to the user's voice channel
                                    await voice_client.move_to(voice_channel)
                                except (discord.ClientException, AttributeError):
                                    pass  # Failed to move, likely due to missing permissions or channel restrictions
                        else:
                            try:
                                # Reconnect to the user's voice channel
                                await voice_client.connect(reconnect=True, timeout=5)
                            except discord.ClientException:
                                pass  # Failed to reconnect, may already be connected elsewhere or missing permissions

                    # User found, break out of the loop
                    break

    #@commands.Cog.listener()
    #async def on_ready(self):
        #await self.follow_user.start()
        


    @follow_user.before_loop
    async def before_follow_user(self):
        await self.bot.wait_until_ready()  # Wait for the bot to be fully ready before starting the loop


async def setup(bot):
    await bot.add_cog(Stalk(bot))
