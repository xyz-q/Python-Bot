import discord
from discord.ext import commands, tasks
import asyncio
import traceback

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_channel_name = "admin-commands" 
        self.trusted_role_id = 1234567890  # Replace with your trusted role ID

    @commands.Cog.listener()
    async def on_ready(self):
        print("\033[93mBot is now operational.\033[0m")
        print("\033[90mLogged in as {0}\033[0m".format(self.bot.user))

        print("\033[0;32mGuilds:\033[0m")
        for guild in self.bot.guilds:
            print("\033[36m- {}\033[0m: {}".format("\033[92m" + str(guild.id) + "\033[0m", "\033[92m" + guild.name + "\033[0m"))

        channel_name = "bot-status"
        channel_type = discord.ChannelType.text
        channel = discord.utils.get(self.bot.get_all_channels(), name=channel_name, type=channel_type)
        if channel:
            try:
                await channel.send(":green_circle: xyz is now online")
                print("\033[90mBOT  IS  READY\033[0m")
            except Exception as e:
                print(f"An error occurred while sending the message: {e}")
        else:
            print("\033[91mChannel not found.\033[0m")

        owner = self.bot.get_user(110927272210354176)
        if owner:
            for guild in self.bot.guilds:
                member = guild.get_member(110927272210354176)
                if member and member.voice:
                    voice_channel = member.voice.channel
                    await voice_channel.connect()
                    break

    @commands.Cog.listener()
    async def on_disconnect(self):
        guild = self.bot.get_guild(1056994840925192252)   
        channel = discord.utils.get(guild.text_channels, name="bot-status")

        if channel and self.bot.is_ready():
            await channel.send(":orange_circle: xyz is experiencing network issues. The bot is still running, but there may be delays in responses.")
        elif channel:
            await channel.send(":red_circle: xyz has been disconnected from Discord's servers. The bot is currently offline.")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        guild = self.bot.get_guild(1056994840925192252)   
        channel = discord.utils.get(guild.text_channels, name="bot-status")

        if channel:
            await channel.send(":orange_circle: Network interruption, attempting to reconnect...")

            error_details = f"An error occurred during the `{event}` event.\n" \
                            f"Error details:\n```{traceback.format_exc()}```"
            await channel.send(error_details)
            await self.bot.close()
            await asyncio.sleep(5)  

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

        if isinstance(error, commands.CommandNotFound):
            if ctx.message.channel.name == self.allowed_channel_name:
                bot_message = await ctx.send(f":warning: Command '{ctx.invoked_with}' not found.")
                print(f"\033[91m  command {ctx.invoked_with} not found.\033[0m")
                await asyncio.sleep(7)
                await bot_message.delete()
            return  # Stop further processing for CommandNotFound errors

        if isinstance(error, commands.MissingRequiredArgument):
            bot_message = await ctx.send("Missing required argument.")
        elif isinstance(error, commands.CheckFailure):  # Check if error is due to channel check failure
            return  # Stop further processing for channel check failures
        else:
            bot_message = await ctx.send("An error occurred.")
            print(f"An error occurred: {error}")

        await asyncio.sleep(7)
        await bot_message.delete()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return  

        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("I can only process commands in a guild. /setup for more info")
            return   

        if message.channel.id == 1234310879072223292 and not message.author.bot:
            await message.delete()
            warning_msg = await message.channel.send(f'{message.author.mention}, sending messages in this channel is not allowed.')
            await asyncio.sleep(4)
            await warning_msg.delete()
            return 

        if message.content.startswith(','):
            if message.content.startswith(',list') or message.content.startswith(',help'):
                await self.bot.process_commands(message)
                return
            
            if not message.content.startswith(',setup'):
                if message.channel.name != self.allowed_channel_name:
                    error_message = ":warning: Commands can only be used in the #admin-commands channel. [/setup]"
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass
                    response = await message.channel.send(error_message)
                    await asyncio.sleep(4)
                    await response.delete()
                    return
                trusted_role = discord.utils.get(message.guild.roles, id=self.trusted_role_id)
                if trusted_role and trusted_role not in message.author.roles:
                    response = await message.channel.send(f" :warning: [ERROR] {message.author.mention} is not permitted to operate commands.")
                    await message.delete()
                    await asyncio.sleep(4)
                    await response.delete()
                    return
                trusted_role = discord.utils.get(message.guild.roles, id=self.trusted_role_id)
                if trusted_role and trusted_role not in message.author.roles:
                    response = await message.channel.send(f" :warning: [ERROR] {message.author.mention} is not permitted to operate commands.")
                    await message.delete()
                    await asyncio.sleep(4)
                    await response.delete()
                    return 
   
        if not message.content.startswith(',') and message.channel.name == self.allowed_channel_name:
            await message.delete()
            warning_msg = await message.channel.send(f'{message.author.mention}, you need to be using a command in this channel.')
            await asyncio.sleep(4)
            await warning_msg.delete()
            return
 

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))
