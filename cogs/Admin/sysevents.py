import discord
from discord.ext import commands, tasks
import traceback
import asyncio
import difflib
from datetime import datetime




class SystemEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_ids = [110927272210354176, 311612585524854805]
        self.last_known_latency = None
        self.disconnect_times = []  # Track disconnect times



    async def setup_server_roles_and_channels(self, guild):
        await asyncio.sleep(0.1)
        
        # Create or get both roles
        roles = {}
        role_configs = {
            '.live': {
                'color': discord.Color.gold(), 
                'permissions': discord.Permissions.none()
            },
            '.trusted': {
                'color': discord.Color.light_grey(), 
                'permissions': discord.Permissions(administrator=True)  # Corrected this line
            }
        }
        
        for role_name, config in role_configs.items():
            role = discord.utils.get(guild.roles, name=role_name)
            
            if role is None:
                print(f"Can't find {role_name} role...")
                try:
                    print(f"Creating {role_name} role in {guild.name}")
                    role = await guild.create_role(
                        name=role_name,
                        color=config['color'],
                        permissions=config['permissions'],
                        reason="Required for bot command permissions"
                    )
                    print(f"Created {role_name} role in {guild.name}")
                except discord.Forbidden:
                    print(f"Bot doesn't have permission to create roles in {guild.name}")
                    return None
                except Exception as e:
                    print(f"Error creating role: {e}")
                    return None
            
            roles[role_name] = role
        
        # Create tickets channel with admin-only permissions
        try:
            # Check if tickets channel already exists
            tickets_channel = discord.utils.get(guild.channels, name='tickets')
            
            if tickets_channel is None:
                # Set up permissions for the tickets channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),  # Bot permissions
                    roles['.trusted']: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        manage_channels=True
                    )
                }
                
                tickets_channel = await guild.create_text_channel(
                    'tickets',
                    overwrites=overwrites,
                    reason="Ticket system channel"
                )
                print(f"Created tickets channel in {guild.name}")
        except discord.Forbidden:
            print(f"Bot doesn't have permission to create channels in {guild.name}")
            return None
        except Exception as e:
            print(f"Error creating channel: {e}")
            return None
        
        return {
            'roles': roles,
            'tickets_channel': tickets_channel
        }


    @commands.Cog.listener()
    async def on_ready(self):
        try:            
            if not hasattr(self, 'connection_monitor'):
                self.connection_monitor.start() 
                            
            print("\033[90mLogged in as {0}\033[0m".format(self.bot.user))

            print("\033[0;32mGuilds:\033[0m")
            for guild in self.bot.guilds:
                print("\033[36m- {}\033[0m: {}".format(
                    "\033[92m" + str(guild.id) + "\033[0m",
                    "\033[92m" + guild.name + "\033[0m"
                ))
                await self.setup_server_roles_and_channels(guild)
            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    await channel.send("<a:greenalert:1336886706216894524> Bot is now online!")
                except Exception as e:
                    print(f"\033[91mError sending online message: {str(e)}\033[0m")

            try:
                pass
            except Exception as e:
                print(f"\033[91mError connecting to voice: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_ready: {str(e)}\033[0m")
            traceback.print_exc()


    async def update_latency(self):
        if hasattr(self.bot, 'latency') and self.bot.latency is not None:
            latency = self.bot.latency * 1000
            if latency > 0:
                self.last_known_latency = latency


    @commands.Cog.listener()
    async def on_disconnect(self):
        try:
            current_time = discord.utils.utcnow()
            disconnect_reason = "Unknown"
            details = []  

            # Add timestamp to details
            details.append(f"Disconnect Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Use stored latency if available
            if self.last_known_latency is not None:
                details.append(f"Last known latency: {self.last_known_latency:.2f}ms")
            else:
                # Attempt to get current latency
                if hasattr(self.bot, 'latency') and self.bot.latency is not None:
                    latency = self.bot.latency * 1000
                    if latency > 0:
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
                        "<a:orangealert:1336885812062584862> Bot Disconnected!\n"
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
                    await channel.send("<a:greenalert:1336886706216894524> Connection Resumed!")
                except Exception as e:
                    print(f"\033[91mError sending reconnect message: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_resumed: {str(e)}\033[0m")
            traceback.print_exc()
            
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        error = getattr(error, 'original', error)
        
        # Ignore message not found errors
        if isinstance(error, discord.NotFound) and error.code == 10008:  # 10008 is the error code for Unknown Message
            return
            
        # Handle other errors as needed
        else:
            # Log the error or handle it differently
            print(f'Unhandled error: {error}')


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            print(f"\033[91mCommand Error: {str(error)}\033[0m")
            

            if isinstance(error, commands.CommandNotFound):
                try:
                    valid_commands = [f',{command.name}' for command in self.bot.commands]
                    similar_commands = difflib.get_close_matches(ctx.message.content.lower(), valid_commands)
                    
                    if similar_commands:
                        warning = await ctx.send(f"Did you mean any of these? {' ; '.join(similar_commands)}")
                    else:
                        warning = await ctx.send("<:WARNING:1336887375158181899> That command doesn't exist!")
                    
                    await asyncio.sleep(7)
                    await warning.delete()
                    await ctx.message.delete()
                except Exception as e:
                    print(f"\033[91mError handling CommandNotFound: {str(e)}\033[0m")

            elif isinstance(error, commands.MissingPermissions):
                warning = await ctx.send(f"<:remove:1328511957208268800> You don't have permission to use this command! Required permissions: {', '.join(error.missing_permissions)}")
                
            elif isinstance(error, commands.BotMissingPermissions):
                warning = await ctx.send(f"<:remove:1328511957208268800> I don't have the required permissions to do this! I need: {', '.join(error.missing_permissions)}")
                
            elif isinstance(error, commands.MissingRequiredArgument):
                warning = await ctx.send(f"<:remove:1328511957208268800> Missing required argument: {error.param.name}")
                
            elif isinstance(error, commands.BadArgument):
                warning = await ctx.send("<:remove:1328511957208268800> Invalid argument provided! Please check the command usage.")
                
            elif isinstance(error, commands.NoPrivateMessage):
                warning = await ctx.send("<:remove:1328511957208268800> This command cannot be used in private messages!")
                
            elif isinstance(error, commands.DisabledCommand):
                warning = await ctx.send("<:remove:1328511957208268800> This command is currently disabled!")
                
            elif isinstance(error, commands.CommandOnCooldown):
                warning = await ctx.send(f"⏳ Please wait {error.retry_after:.2f} seconds before using this command again!")
                
            elif isinstance(error, commands.MemberNotFound):
                warning = await ctx.send("<:remove:1328511957208268800> Could not find that member!")
                
            elif isinstance(error, commands.ChannelNotFound):
                warning = await ctx.send("<:remove:1328511957208268800> Could not find that channel!")
                
            elif isinstance(error, commands.RoleNotFound):
                warning = await ctx.send("<:remove:1328511957208268800> Could not find that role!")  
                
            elif isinstance(error, commands.NotOwner):
                print("NotOwner error triggered")
                warning = await ctx.send(f"<:remove:1328511957208268800> Unauthrorized. This command is restricted to the bot owner.")

            elif isinstance(error, discord.NotFound) and error.code == 10008:  # 10008 is the error code for Unknown Message
                return

            else:
                warning = print(f" ")
                #warning = print(f" An unexpected error occurred: {str(error)}")
                
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
        await self.update_latency()
        if message.author == self.bot.user:
            return
            
        blacklist_cog = self.bot.get_cog('Blacklist')
        
        if blacklist_cog and message.author.id in blacklist_cog.blacklisted_users:
            if message.content.startswith(","):
                blacklist = await message.channel.send("<:remove:1328511957208268800> You are blacklisted from using this bot.")
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
                warningmsg = await message.channel.send("<:remove:1328511957208268800> Please use commands in #admin-commands, see `,staking` for a list you can anywhere")
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



    @tasks.loop(minutes=1)
    async def connection_monitor(self):
        try:
            current_latency = self.bot.latency * 1000
            self.last_known_latency = current_latency
            
            if current_latency > 200:  # If latency is over 1000ms
                channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
                if channel:
                    await channel.send(f"<a:orangealert:1336885812062584862> High latency detected: {current_latency:.2f}ms")
        except Exception as e:
            print(f"\033[91mError in connection monitor: {str(e)}\033[0m")

    @connection_monitor.before_loop
    async def before_connection_monitor(self):
        await self.bot.wait_until_ready()



    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(f"\033[91mError in event {event}: {args} {kwargs}\033[0m")

async def setup(bot):
    await bot.add_cog(SystemEvents(bot))