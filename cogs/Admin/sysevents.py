import discord
from discord.ext import commands, tasks
import traceback
import asyncio
import difflib
import json
import os
from datetime import datetime, timezone, timedelta


STATUS_FILE = ".json/status_message.json"


class SystemEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_known_latency = None
        self.incidents = []  # {"type": str, "time": datetime, "detail": str}
        self.status_message_id = None
        self.status_channel_id = None
        self._load_status_message_id()
        self.connection_monitor.start()
        self.channel_cleanup.start()

    def _load_status_message_id(self):
        try:
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                self.status_message_id = data.get("message_id")
                self.status_channel_id = data.get("channel_id")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_status_message_id(self):
        os.makedirs(".json", exist_ok=True)
        with open(STATUS_FILE, 'w') as f:
            json.dump({"message_id": self.status_message_id, "channel_id": self.status_channel_id}, f)

    def _prune_incidents(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self.incidents = [i for i in self.incidents if i["time"] > cutoff]

    def _build_status_embed(self):
        self._prune_incidents()
        latency = f"{self.last_known_latency:.2f}ms" if self.last_known_latency else "Unknown"

        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Status", value="🟢 Online", inline=True)
        embed.add_field(name="Latency", value=latency, inline=True)

        if self.incidents:
            lines = []
            recent = list(reversed(self.incidents))[:4]
            for inc in recent:
                ts = inc["time"].strftime("%H:%M:%S UTC")
                if inc["type"] == "disconnect":
                    lines.append(f"🔴 `{ts}` Disconnected — {inc['detail']}")
                elif inc["type"] == "resume":
                    lines.append(f"🟢 `{ts}` Reconnected")
                elif inc["type"] == "high_latency":
                    lines.append(f"🟡 `{ts}` High latency started — {inc['detail']}")
                elif inc["type"] == "high_latency_end":
                    lines.append(f"🟢 `{ts}` High latency resolved — {inc['detail']}")
            total = len(self.incidents)
            if total > 4:
                lines.append(f"\n+{total - 4} more incidents in the last 24h")
            embed.add_field(name="Incidents (last 24h)", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="Incidents (last 24h)", value="None", inline=False)

        embed.set_footer(text="Last updated")
        return embed

    async def _get_status_channel(self):
        return discord.utils.get(self.bot.get_all_channels(), name='bot-status')

    async def _update_status_message(self):
        try:
            channel = await self._get_status_channel()
            if not channel:
                return

            embed = self._build_status_embed()

            if self.status_message_id and self.status_channel_id == channel.id:
                try:
                    msg = await channel.fetch_message(self.status_message_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound:
                    pass

            msg = await channel.send(embed=embed)
            self.status_message_id = msg.id
            self.status_channel_id = channel.id
            self._save_status_message_id()
        except Exception as e:
            print(f"\033[91mError updating status message: {e}\033[0m")

    async def setup_server_roles_and_channels(self, guild):
        await asyncio.sleep(0.1)
        roles = {}
        role_configs = {
            '.live': {
                'color': discord.Color.red(),
                'permissions': discord.Permissions.none()
            },
            '.trusted': {
                'color': discord.Color.gold(),
                'permissions': discord.Permissions(administrator=True)
            },
            '.afk': {
                'color': discord.Color.lighter_gray(),
                'permissions': discord.Permissions.none()
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

        try:
            tickets_channel = discord.utils.get(guild.channels, name='tickets')
            if tickets_channel is None:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
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

        return {'roles': roles, 'tickets_channel': tickets_channel}

    async def sync_afk_roles(self, guild):
        try:
            import os
            AFK_FILE = ".json/afk_data.json"
            if not os.path.exists(AFK_FILE):
                return
            with open(AFK_FILE, 'r') as file:
                afk_users = json.load(file)

            afk_role = discord.utils.get(guild.roles, name='.afk')
            if not afk_role:
                return

            for user_id in afk_users:
                member = guild.get_member(int(user_id))
                if member:
                    if afk_role not in member.roles:
                        try:
                            await member.add_roles(afk_role)
                            print(f"Added .afk role to {member.name} (sync)")
                        except discord.Forbidden:
                            pass
                    if member.nick and not member.nick.startswith("{afk}"):
                        try:
                            new_nickname = f"{{afk}} {member.nick}"
                            if len(new_nickname) > 32:
                                new_nickname = new_nickname[:32]
                            await member.edit(nick=new_nickname)
                            print(f"Added {{afk}} tag to {member.name} (sync)")
                        except discord.Forbidden:
                            pass
        except Exception as e:
            print(f"Error syncing AFK roles: {e}")

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
                await self.setup_server_roles_and_channels(guild)
                await self.sync_afk_roles(guild)
            await self._update_status_message()
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
            detail = f"latency {self.last_known_latency:.2f}ms" if self.last_known_latency else "latency unknown"
            self.incidents.append({
                "type": "disconnect",
                "time": datetime.now(timezone.utc),
                "detail": detail
            })
            print(f"\033[93mBot disconnected — {detail}\033[0m")
            await self._update_status_message()
        except Exception as e:
            print(f"\033[91mError in on_disconnect: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_resumed(self):
        try:
            self.incidents.append({
                "type": "resume",
                "time": datetime.now(timezone.utc),
                "detail": ""
            })
            print("\033[92mConnection Resumed\033[0m")
            await self._update_status_message()
        except Exception as e:
            print(f"\033[91mError in on_resumed: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        error = getattr(error, 'original', error)
        if isinstance(error, discord.NotFound) and error.code == 10008:
            return
        print(f'Unhandled app command error: {error}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            print(f"\033[91mCommand Error: {str(error)}\033[0m")
            warning = None

            if isinstance(error, commands.CommandNotFound):
                try:
                    valid_commands = [f',{command.name}' for command in self.bot.commands]
                    similar_commands = difflib.get_close_matches(ctx.message.content.lower(), valid_commands)
                    if similar_commands:
                        formatted_commands = ' ; '.join(f'`{cmd}`' for cmd in similar_commands)
                        warning = await ctx.send(f"Did you mean any of these? {formatted_commands}")
                    else:
                        warning = await ctx.send("<:WARNING:1336887375158181899> That command doesn't exist!")
                    await asyncio.sleep(7)
                    await warning.delete()
                    await ctx.message.delete()
                except Exception as e:
                    print(f"\033[91mError handling CommandNotFound: {str(e)}\033[0m")
                return

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
                warning = await ctx.send("<:remove:1328511957208268800> Unauthorized. This command is restricted to the bot owner.")
            elif isinstance(error, discord.NotFound) and error.code == 10008:
                return
            else:
                print(f"\033[91mUnhandled error: {str(error)}\033[0m")
                traceback.print_exc()

            try:
                if warning is not None:
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
                print(f"\033[0;32mDM from {message.author}: {message.content}\033[0m")
                return

            allowed_commands = (',pc', ',help', ',invite', ',slots', ',flower', ',bal', ',balance', ',staking', ',deposit', ',withdraw', ',stats', ',transfer', ',send', ',cf', ',pvpflip', ',ticket', ',vault', ',accept', ',profile', ',history', ',transactions', ',notification', ',alchables')

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

            content_lower = message.content.lower()

            if content_lower.startswith(allowed_commands):
                print(f"\033[0;32mAllowed Command: {message.content} by {message.author}\033[0m")
                await self.bot.process_commands(message)
                return

            try:
                warningmsg = await message.channel.send("<:remove:1328511957208268800> Please use commands in #admin-commands, see `,staking` for a list you can anywhere")
                print(f"\033[91m User {message.author} tried to use command: {message.content} outside of #admin-commands \033[0m")
                await message.delete()
                await asyncio.sleep(7)
                await warningmsg.delete()
            except Exception as e:
                print(f"\033[91mError handling wrong channel: {str(e)}\033[0m")
            return

        except Exception as e:
            print(f"\033[91mError in on_message: {str(e)}\033[0m")
            traceback.print_exc()

    @commands.command()
    @commands.is_owner()
    async def testsys(self, ctx, event_type: str = "disconnect", code: int = None):
        """Test system events. Usage: ,testsys <disconnect|resume> [code]"""
        try:
            if event_type.lower() == "disconnect":
                if code:
                    class MockWebSocket:
                        def __init__(self, close_code):
                            self.close_code = close_code
                    original_ws = self.bot._connection._ws if hasattr(self.bot._connection, '_ws') else None
                    self.bot._connection._ws = MockWebSocket(code)
                    try:
                        await ctx.send(f"Testing disconnect event with code {code}...")
                        await self.on_disconnect()
                    finally:
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

    @tasks.loop(minutes=5)
    async def channel_cleanup(self):
        try:
            channel = await self._get_status_channel()
            if not channel or not self.status_message_id:
                return
            async for msg in channel.history(limit=100):
                if msg.id != self.status_message_id:
                    try:
                        await msg.delete()
                        await asyncio.sleep(0.5)
                    except (discord.Forbidden, discord.NotFound):
                        pass
        except Exception as e:
            print(f"\033[91mError in channel cleanup: {e}\033[0m")

    @channel_cleanup.before_loop
    async def before_channel_cleanup(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def connection_monitor(self):
        try:
            current_latency = self.bot.latency * 1000
            self.last_known_latency = current_latency

            if current_latency > 200:
                # Only log when high latency starts
                last = next((i for i in reversed(self.incidents) if i["type"] in ("high_latency", "high_latency_end")), None)
                if last is None or last["type"] == "high_latency_end":
                    self.incidents.append({
                        "type": "high_latency",
                        "time": datetime.now(timezone.utc),
                        "detail": f"{current_latency:.2f}ms"
                    })
            else:
                # Log when high latency ends
                last = next((i for i in reversed(self.incidents) if i["type"] in ("high_latency", "high_latency_end")), None)
                if last and last["type"] == "high_latency":
                    self.incidents.append({
                        "type": "high_latency_end",
                        "time": datetime.now(timezone.utc),
                        "detail": f"{current_latency:.2f}ms"
                    })

            await self._update_status_message()
        except Exception as e:
            print(f"\033[91mError in connection monitor: {str(e)}\033[0m")

    @connection_monitor.before_loop
    async def before_connection_monitor(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.connection_monitor.cancel()
        self.channel_cleanup.cancel()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(f"\033[91mError in event {event}: {args} {kwargs}\033[0m")


async def setup(bot):
    await bot.add_cog(SystemEvents(bot))
