import discord
from discord.ext import commands
import traceback
import asyncio
import difflib
from datetime import datetime




class SystemEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_ids = [110927272210354176, 311612585524854805]


    async def get_or_create_trusted_role(self, guild):
        await asyncio.sleep(0.1)
        
        trusted_role = discord.utils.get(guild.roles, name='.trusted')
        
        if trusted_role is None:
            print("Can't find trusted role...")
            try:
                print(f"Creating .trusted role in {guild.name}")
                trusted_role = await guild.create_role(
                    name='.trusted',
                    color=discord.Color.gold(),
                    reason="Required for bot command permissions"
                )
                print(f"Created .trusted role in {guild.name}")
            except discord.Forbidden:
                print(f"Bot doesn't have permission to create roles in {guild.name}")
                return None
            except Exception as e:
                print(f"Error creating role: {e}")
                return None
                
        return trusted_role

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            
            
            print("\033[90mLogged in as {0}\033[0m".format(self.bot.user))

            print("\033[0;32mGuilds:\033[0m")
            for guild in self.bot.guilds:
                print("\033[36m- {}\033[0m: {}".format(
                    "\033[92m" + str(guild.id) + "\033[0m",
                    "\033[92m" + guild.name + "\033[0m"
                ))
                await self.get_or_create_trusted_role(guild)
            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    await channel.send("🟢 Bot is now online!")
                except Exception as e:
                    print(f"\033[91mError sending online message: {str(e)}\033[0m")

            try:
                pass
            except Exception as e:
                print(f"\033[91mError connecting to voice: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_ready: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            current_time = discord.utils.utcnow()
            disconnect_reason = "Unknown"
            details = []  

            # Add timestamp to details
            details.append(f"Disconnect Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Add latency info - with validation
            if hasattr(self.bot, 'latency') and self.bot.latency is not None:
                latency = self.bot.latency * 1000
                if latency > 0:  # Only add if we have a valid latency
                    details.append(f"Last known latency: {latency:.2f}ms")
                else:
                    details.append("Last known latency: Not available")
            else:
                details.append("Last known latency: Not available")

            # Improved WebSocket close code handling
            if hasattr(self.bot, '_connection') and hasattr(self.bot._connection, '_ws'):
                ws = self.bot._connection._ws
                if hasattr(ws, 'close_code') and ws.close_code is not None:
                    code_meanings = {
                        1000: "Normal closure",
                        1001: "Going away",
                        1006: "Abnormal closure",
                        1011: "Internal error",
                        1012: "Service restart",
                        4000: "Unknown error",
                        4001: "Unknown opcode",
                        4002: "Decode error",
                        4003: "Not authenticated",
                        4004: "Authentication failed",
                        4005: "Already authenticated",
                        4007: "Invalid sequence",
                        4008: "Rate limited",
                        4009: "Session timeout",
                        4010: "Invalid shard",
                        4011: "Sharding required",
                        4012: "Invalid API version",
                        4013: "Invalid intent(s)",
                        4014: "Disallowed intent(s)"
                    }
                    close_code = ws.close_code
                    disconnect_reason = code_meanings.get(close_code, f"Unknown close code: {close_code}")
                    details.append(f"Close code: {close_code} ({disconnect_reason})")
                else:
                    disconnect_reason = "No close code available"
                    details.append("Close code: Not available")
            else:
                disconnect_reason = "WebSocket connection not found"
                details.append("Connection details: Not available")

            # Console output with better formatting
            print("\n" + "="*50)
            print(f"\033[93mBot Disconnect Event\033[0m")
            print(f"\033[93mReason: {disconnect_reason}\033[0m")
            for detail in details:
                print(f"\033[93m- {detail}\033[0m")
            print("="*50 + "\n")

            # Discord channel notification
            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    disconnect_msg = (
                        "🔴 Bot Disconnected!\n"
                        f"Reason: {disconnect_reason}\n"
                        + "\n".join(f"• {detail}" for detail in details)
                    )
                    await channel.send(disconnect_msg)
                except Exception as e:
                    print(f"\033[91mError sending disconnect message: {str(e)}\033[0m")
                    traceback.print_exc()

        except Exception as e:
            print(f"\033[91mError in on_disconnect: {str(e)}\033[0m")
            traceback.print_exc()


    @commands.Cog.listener()
    async def on_resumed(self):
        """Handle reconnection after disconnect"""
        try:
            print("\033[92mConnection Resumed\033[0m")
            


            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    await channel.send("🟢 Connection Resumed!")
                except Exception as e:
                    print(f"\033[91mError sending reconnect message: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_resumed: {str(e)}\033[0m")
            traceback.print_exc()


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            print(f"\033[91mCommand Error: {str(error)}\033[0m")
            traceback.print_exc()

            if isinstance(error, commands.CommandNotFound):
                try:
                    valid_commands = [f',{command.name}' for command in self.bot.commands]
                    similar_commands = difflib.get_close_matches(ctx.message.content.lower(), valid_commands)
                    
                    if similar_commands:
                        warning = await ctx.send(f"Did you mean any of these? {' ; '.join(similar_commands)}")
                    else:
                        warning = await ctx.send("⚠️ That command doesn't exist!")
                    
                    await asyncio.sleep(7)
                    await warning.delete()
                    await ctx.message.delete()
                except Exception as e:
                    print(f"\033[91mError handling CommandNotFound: {str(e)}\033[0m")

            elif isinstance(error, commands.MissingPermissions):
                warning = await ctx.send(f"❌ You don't have permission to use this command! Required permissions: {', '.join(error.missing_permissions)}")
                
            elif isinstance(error, commands.BotMissingPermissions):
                warning = await ctx.send(f"❌ I don't have the required permissions to do this! I need: {', '.join(error.missing_permissions)}")
                
            elif isinstance(error, commands.MissingRequiredArgument):
                warning = await ctx.send(f"❌ Missing required argument: {error.param.name}")
                
            elif isinstance(error, commands.BadArgument):
                warning = await ctx.send("❌ Invalid argument provided! Please check the command usage.")
                
            elif isinstance(error, commands.NoPrivateMessage):
                warning = await ctx.send("❌ This command cannot be used in private messages!")
                
            elif isinstance(error, commands.DisabledCommand):
                warning = await ctx.send("❌ This command is currently disabled!")
                
            elif isinstance(error, commands.CommandOnCooldown):
                warning = await ctx.send(f"⏳ Please wait {error.retry_after:.2f} seconds before using this command again!")
                
            elif isinstance(error, commands.MemberNotFound):
                warning = await ctx.send("❌ Could not find that member!")
                
            elif isinstance(error, commands.ChannelNotFound):
                warning = await ctx.send("❌ Could not find that channel!")
                
            elif isinstance(error, commands.RoleNotFound):
                warning = await ctx.send("❌ Could not find that role!")  
                
            elif isinstance(error, commands.NotOwner):
                print("NotOwner error triggered")
                warning = await ctx.send(f"❌ You are not <@110927272210354176>")


            else:
                warning = print(f"⚠️ An unexpected error occurred: {str(error)}")
                
            try:
                await asyncio.sleep(7)
                await warning.delete()
                if ctx.message:
                    await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound, AttributeError):
                pass

        except Exception as e:
            print(f"\033[91mError in error handler: {str(e)}\033[0m")
            traceback.print_exc()



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
            
        blacklist_cog = self.bot.get_cog('Blacklist')
        
        if blacklist_cog and message.author.id in blacklist_cog.blacklisted_users:
            if message.content.startswith(","):
                blacklist = await message.channel.send("❌ You are blacklisted from using this bot.")
                await message.delete()
                await asyncio.sleep(4)
                await blacklist.delete()
                return
            


        try:
            if isinstance(message.channel, discord.DMChannel):
                try:
                    print(f"\033[0;32mDM from {message.author}: {message.content}\033[0m")
                    return
                except Exception as e:
                    print(f"\033[91mError handling DM: {str(e)}\033[0m")
                    return

            allowed_commands = (',pc', ',help', ',invite', ',slots', ',flower', ',bal', ',balance', ',staking', ',deposit', ',withdraw', ',stats', ',transfer', ',send', ',cf', ',pvpflip', ',ticket', ',vault', ',accept', ',profile', ',history', ',transactions', ',notification')

            if not message.content.startswith(','):
                return

            if message.author.id == 110927272210354176:
                await self.bot.process_commands(message)
                print(f"\033[0;32mOwner Command: {message.content} by {message.author}\033[0m")
                return

            if message.channel.name == 'admin-commands':
                print(f"\033[0;32mAdmin Command: {message.content} by {message.author}\033[0m")
                await self.bot.process_commands(message)
                return

            if message.content.startswith(','):
                message.content = message.content.lower() 
                print(f"\033[0;32mCommand: {message.content} by {message.author}\033[0m")
                
            if message.content.startswith(allowed_commands):
                print(f"\033[0;32mAllowed Command: {message.content} by {message.author}\033[0m")
                await self.bot.process_commands(message)
                return

            try:
                warningmsg = await message.channel.send("❌ Please use commands in #admin-commands, see `,staking` for a list you can anywhere")
                print(f"\033[91m User {message.author} tried to use command: {message.content} outside of #admin-commands \033[0m")
                await message.delete()
                await asyncio.sleep(7)
                
                await warningmsg.delete()
                return
            except Exception as e:
                print(f"\033[91mError handling wrong channel: {str(e)}\033[0m")
            
 
            await self.bot.process_commands(message)

        except Exception as e:
            print(f"\033[91mError in on_message: {str(e)}\033[0m")
            traceback.print_exc()



    @commands.command()
    @commands.is_owner()
    async def testsys(self, ctx, event_type: str = "disconnect", code: int = None):
        """Test system events
        Usage: ,testsys <disconnect|resume> [code]"""
        try:
            if event_type.lower() == "disconnect":
                if code:
                    # Create a mock WebSocket close code
                    class MockWebSocket:
                        def __init__(self, close_code):
                            self.close_code = close_code

                    # Store the original ws
                    original_ws = self.bot._connection._ws if hasattr(self.bot._connection, '_ws') else None
                    
                    # Set our mock ws with the test code
                    self.bot._connection._ws = MockWebSocket(code)
                    
                    await ctx.send(f"Testing disconnect event with code {code}...")
                    await self.on_disconnect()
                    
                    # Restore original ws
                    self.bot._connection._ws = original_ws
                else:
                    await ctx.send("Testing normal disconnect event...")
                    await self.on_disconnect()
                
            elif event_type.lower() == "resume":
                await ctx.send("Testing resume event...")
                await self.on_resumed()
                
            else:
                await ctx.send("Invalid event type. Use 'disconnect' or 'resume'")
                
        except Exception as e:
            await ctx.send(f"Error during test: {str(e)}")




    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(f"\033[91mError in event {event}: {args} {kwargs}\033[0m")

async def setup(bot):
    await bot.add_cog(SystemEvents(bot))