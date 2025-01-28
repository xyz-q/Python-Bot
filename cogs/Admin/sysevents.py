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
            self.disconnect_count += 1
            current_time = discord.utils.utcnow()
            
            # Determine disconnect reason
            disconnect_reason = "Unknown"
            details = []

            # Check if we lost connection due to heartbeat timeout
            if self.last_heartbeat:
                time_since_heartbeat = (current_time - self.last_heartbeat).total_seconds()
                if time_since_heartbeat > 41.25:  # Discord heartbeat interval is 41.25 seconds
                    disconnect_reason = "Heartbeat Timeout"
                    details.append(f"Last heartbeat was {time_since_heartbeat:.2f} seconds ago")

            # Check bot's latency before disconnect
            if self.bot.latency:
                details.append(f"Last known latency: {self.bot.latency * 1000:.2f}ms")

            # Check if we have any websocket close code
            if hasattr(self.bot, '_connection') and hasattr(self.bot._connection, '_ws'):
                ws = self.bot._connection._ws
                if hasattr(ws, 'close_code'):
                    code_meanings = {
                        1000: "Normal closure",
                        1001: "Going away",
                        1006: "Abnormal closure",
                        1009: "Message too big",
                        1011: "Internal error",
                        1012: "Service restart",
                        4000: "Unknown error",
                        4001: "Unknown opcode",
                        4002: "Decode error",
                        4003: "Not authenticated",
                        4004: "Authentication failed",
                        4005: "Already authenticated",
                        4007: "Invalid seq",
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
                    details.append(f"Close code: {close_code}")

            # Log disconnect details
            print(f"\033[93mBot Disconnect #{self.disconnect_count}\033[0m")
            print(f"\033[93mReason: {disconnect_reason}\033[0m")
            for detail in details:
                print(f"\033[93m- {detail}\033[0m")

            # Try to send disconnect message to status channel
            channel = discord.utils.get(self.bot.get_all_channels(), name='bot-status')
            if channel:
                try:
                    embed = discord.Embed(
                        title="🔴 Bot Disconnected",
                        color=discord.Color.red(),
                        timestamp=current_time
                    )
                    embed.add_field(
                        name="Disconnect Info",
                        value=f"**Reason:** {disconnect_reason}\n" +
                            "\n".join([f"• {detail}" for detail in details])
                    )
                    embed.set_footer(text=f"Disconnect #{self.disconnect_count}")
                    
                    # Store message for potential reconnect update
                    self.last_disconnect_message = await channel.send(embed=embed)
                    
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
            
            # Update the last disconnect message if it exists
            if hasattr(self, 'last_disconnect_message'):
                try:
                    embed = self.last_disconnect_message.embeds[0]
                    embed.add_field(
                        name="Reconnected",
                        value=f"Bot reconnected at {discord.utils.utcnow().strftime('%H:%M:%S UTC')}",
                        inline=False
                    )
                    embed.color = discord.Color.orange()
                    await self.last_disconnect_message.edit(embed=embed)
                except Exception as e:
                    print(f"\033[91mError updating disconnect message: {str(e)}\033[0m")

            # Send new reconnect message
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
    async def on_socket_raw_receive(self, msg):
        # Track last heartbeat acknowledgment
        if msg and 'heartbeat_ack' in str(msg):
            self.last_heartbeat = discord.utils.utcnow()    

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            # Log all command errors
            print(f"\033[91mCommand Error: {str(error)}\033[0m")
            traceback.print_exc()

            if isinstance(error, commands.CommandNotFound):
                try:
                    # Get similar commands
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
                
            elif isinstance(error, commands.CheckFailure):
                warning = await ctx.send("❌ You don't have permission to use this command!")

            else:
                # Handle any unhandled errors
                warning = await ctx.send(f"⚠️ An unexpected error occurred: {str(error)}")
                
            # Clean up error messages after delay
            try:
                await asyncio.sleep(7)
                await warning.delete()
                if ctx.message:
                    await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound, AttributeError):
                pass  # Ignore if messages are already deleted or can't be deleted

        except Exception as e:
            print(f"\033[91mError in error handler: {str(e)}\033[0m")
            traceback.print_exc()


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        

        try:
            # Handle DMs
            if isinstance(message.channel, discord.DMChannel):
                try:
                    print(f"\033[0;32mDM from {message.author}: {message.content}\033[0m")
                    return
                except Exception as e:
                    print(f"\033[91mError handling DM: {str(e)}\033[0m")
                    return


            allowed_commands = (',pc', ',help', ',invite', ',slots', ',flower', ',bal', ',balance', ',staking', ',deposit', ',withdraw', ',stats', ',transfer', ',send', ',cf', ',pvpflip', ',ticket')

            # Only process commands that start with ','
            if not message.content.startswith(','):
                return
            if message.content.startswith(', '):
                message.content = message.content.lower()
                print(f"\033[0;32mCommand: {message.content} by {message.author}\033[0m")
                
            # Allow admin to use any command anywhere
            if message.author.id == 110927272210354176:
                await self.bot.process_commands(message)
                print(f"\033[0;32mOwner Command: {message.content} by {message.author}\033[0m")
                return

            # If in admin-commands channel, let the normal command handler process it
            if message.channel.name == 'admin-commands':
                return  # Let the normal command handler handle it

            # Handle allowed commands in other channels
            if message.content.startswith(allowed_commands):
                await self.bot.process_commands(message)

                return

            # If it's not an allowed command and not in admin-commands, warn the user
            try:
                warning = await message.channel.send("❌ Please use commands in #admin-commands")
                print(f"\033[91m User {message.author} tried to use command: {message.content} outside of #admin-commands \033[0m")
                await asyncio.sleep(7)
                await message.delete()
                await warning.delete()
            except Exception as e:
                print(f"\033[91mError handling wrong channel: {str(e)}\033[0m")

        except Exception as e:
            print(f"\033[91mError in on_message: {str(e)}\033[0m")
            traceback.print_exc()






    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(f"\033[91mError in event {event}: {args} {kwargs}\033[0m")

async def setup(bot):
    await bot.add_cog(SystemEvents(bot))