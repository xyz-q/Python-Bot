import discord
from discord.ext import commands
import traceback
import asyncio
import difflib

class SystemEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            print("\033[93mBot is now operational.\033[0m")
            print("\033[90mLogged in as {0}\033[0m".format(self.bot.user))

            print("\033[0;32mGuilds:\033[0m")
            for guild in self.bot.guilds:
                print("\033[36m- {}\033[0m: {}".format(
                    "\033[92m" + str(guild.id) + "\033[0m",
                    "\033[92m" + guild.name + "\033[0m"
                ))

            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    await channel.send("🟢 Bot is now online!")
                except Exception as e:
                    print(f"\033[91mError sending online message: {str(e)}\033[0m")

            # If you have voice channel connection code, wrap it in try/except
            try:
                # Your voice channel connection code here
                pass
            except Exception as e:
                print(f"\033[91mError connecting to voice: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_ready: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            print("\033[93mBot has disconnected from Discord.\033[0m")
            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    await channel.send("🟠 Bot has disconnected!")
                except Exception as e:
                    print(f"\033[91mError sending disconnect message: {str(e)}\033[0m")
        except Exception as e:
            print(f"\033[91mError in on_disconnect: {str(e)}\033[0m")
            traceback.print_exc()



    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            # Log all command errors
            print(f"\033[91mCommand Error: {str(error)}\033[0m")
            traceback.print_exc()

            if isinstance(error, commands.CommandNotFound):
                try:
                    # Retrieve all command names
                    valid_commands = [f',{command.name}' for command in self.bot.commands]
                    similar_commands = difflib.get_close_matches(ctx.message.content.lower(), valid_commands)
                    
                    if similar_commands:
                        suggestion = f"Did you mean any of these? {' ; '.join(similar_commands)}"
                        warning = await ctx.send(suggestion)
                    else:
                        warning = await ctx.send("⚠️ That command doesn't exist!")
                    
                    await asyncio.sleep(7)
                    await warning.delete()
                    await ctx.message.delete()
                except Exception as e:
                    print(f"\033[91mError handling CommandNotFound: {str(e)}\033[0m")
            else:
                # Handle other types of errors
                try:
                    warning = print(f"⚠️ An error occurred: {str(error)}")

                except Exception as e:
                    print(f"\033[91mError sending error message: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in error handler: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        try:
            if isinstance(message.channel, discord.DMChannel):
                try:
                    await message.channel.send("❌ I don't respond to DMs!")
                    return
                except Exception as e:
                    print(f"\033[91mError handling DM: {str(e)}\033[0m")
                    return
            message.content = message.content.lower()         
            
            if message.content.startswith(','):
                print(f"\033[0;32mCommand: {message.content} by {message.author}\033[0m")
                return
                
            if message.content.startswith((',pc', ',help', ',invite', ',slots', ',flower', ',bal', ',balance', ',staking', ',deposit', ',withdraw', ',stats', ',transfer', ',send')):
                print(f"\033[0;32mCommand has been bypassed properly.\033[0m")
                await self.bot.process_commands(message)
                return

            if message.channel.name != 'admin-commands':
                try:
                    if message.author.id == 110927272210354176:
                        await self.bot.process_commands(message)
                        print("Processing command from owner..")
                        return
                    warning = await message.channel.send("❌ Please use commands in #admin-commands")
                    print(f"\033[91m User {message.author} tried to use command: {message.content} outside of #admin-commands \033[0m")
                    await asyncio.sleep(7)
                    await message.delete()
                    await warning.delete()
                except Exception as e:
                    print(f"\033[91mError handling wrong channel: {str(e)}\033[0m")
                return

            await self.bot.process_commands(message)
            print("Processing command..")

        except Exception as e:
            print(f"\033[91mError in on_message: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(f"\033[91mError in event {event}: {args} {kwargs}\033[0m")

async def setup(bot):
    await bot.add_cog(SystemEvents(bot))
