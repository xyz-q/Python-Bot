from discord.ext import commands
import discord
import asyncio

commands_list = [
    # kill.py > AdminCog
    (",kill", "KILLS THE BOT [restricted command]"),
    
    # admincmds.py > AdminCommands
    (",audit <#>", "Displays audit logs"),
    (",autodelete", "Toggles the bot's autodelete function"),
    (",hello", "Hello world command"),
    (",kick <@user(s)> <reason>", "Kicks the user(s) from the server"),
    (",kill2", "Alternative bot termination command [restricted]"),
    (",ping", "Ping command - Test if the bot is responsive- displays the latency from the bot to the server"),
    
    # alchables.py > Alchables
    (",alchables", "Displays best high alch items based on wiki data by volume"),
    
    # publish.py > AutoPublish
    (",checkpublish", "Check publishing configuration for current channel"),
    (",cleanup_status", "Check the status of the cleanup task"),
    (",publish", "Start auto-publishing messages in the current channel"),
    (",publishing", "Check which channels have auto-publishing enabled"),
    (",set_cleanup_interval <minutes>", "Set the cleanup task interval in minutes"),
    (",stoppublish", "Stop auto-publishing messages in the current channel"),
    (",toggle_cleanup", "Toggle the automatic cleanup task"),
    
    # ban.py > BanSystem
    (",ban <@member> <reason> <delete_messages>", "Ban a member from the server"),
    
    # gamblebj.py > Blackjack
    (",blackjack <amount>", "Play blackjack with betting"),
    
    # blacklist.py > Blacklist
    (",blacklist <@user>", "Add or remove user from blacklist"),
    
    # bosscmd.py > BossDrops
    (",add_drops", "Interactive command to add boss drops"),
    (",simulate <boss_name> <kill_count>", "Simulate kills for a given boss"),
    
    # bugreport.py > BugReport
    (",bugreport", "Open the bug report form"),
    (",viewbugs", "View all bug reports [owner only]"),
    
    # cs2_updates.py > CS2Updates
    (",cs2clear", "Clear last update ID to reset tracking [owner only]"),
    (",cs2notify", "Toggle CS2 update notifications in DMs"),
    (",cs2status", "Check CS2 update tracking status [owner only]"),
    (",cs2updates", "Get the latest CS2 patch notes from Steam"),
    (",testcs2dm", "Test CS2 update DM notification [owner only]"),
    
    # chatcmds.py > ChatCommands
    (",mock <@user>", "Toggle mocking of target user"),
    (",purge <limit> <#channel>", "Delete messages in channel, default is 10"),
    (",say <#channel> 'TEXT'", "Makes the bot chat the desired text in specified channel"),
    
    # checkhtml.py > CheckHTML
    (",checkhtml <url> <search_term>", "Check HTML structure of any website"),
    
    # cogs.py > CogLister
    (",listcogs", "Lists all cogs"),
    
    # coinflip.py > CoinFlip
    (",coinflip", "Flip a coin - heads or tails"),
    
    # compare_commands.py > CommandComparison
    (",compare", "Compare actual commands with hardcoded list"),
    
    # cooldown.py > CommandLock
    (",another_task", "Another task command"),
    (",long_task", "Long running task command"),
    
    # commandstats.py > CommandStats
    (",mystats", "Display your command usage statistics"),
    
    # dms.py > DMCommands
    (",dm <@user> <message>", "Send a message to target user"),
    (",dms <@user>", "Show the bot's DMs with a user"),
    
    # downtime.py > DowntimeCog
    (",downtime", "Check bot downtime information"),
    
    # gamble.py > Economy
    (",accept", "Accept a trade or transaction"),
    (",add <amount>", "Add currency to account"),
    (",balance", "Check your balance"),
    (",balancelist", "List all user balances"),
    (",clearcurrency", "Clear all currency data"),
    (",cleartransactions", "Clear transaction history"),
    (",flower", "Flower poker gambling game"),
    (",housestats", "Display house gambling statistics"),
    (",limits", "Show gambling limits"),
    (",pvpflip", "PvP coin flip gambling"),
    (",remove <amount>", "Remove currency from account"),
    (",resetstats", "Reset gambling statistics"),
    (",setbalance <amount>", "Set account balance"),
    (",slots", "Play slot machine"),
    (",staking", "Staking gambling game"),
    (",stats", "Display gambling statistics"),
    (",transactions", "View transaction history"),
    (",transfer <@user> <amount>", "Transfer currency to another user"),
    (",vault", "Access your vault"),
    
    # elynotify.py > ElyNotify
    (",alerts", "View your RS3 price alerts"),
    (",myalerts", "Display user's alerts"),
    (",notify <item> <price> <h/l>", "Set price alert for RS3 item"),
    (",removealert <item>", "Remove alert for specific item"),
    
    # emoji.py > EmojiCommands
    (",emoji", "Get details of an emoji"),
    (",emojiadd <link>", "Create an emoji from link"),
    (",emojiremove <name>", "Delete an emoji"),
    (",emojis", "List server emojis"),
    
    # errortest.py > ErrorTest
    (",attribute_error", "Test attribute error"),
    (",check_fail", "Test check failure"),
    (",divide_by_zero", "Test division by zero error"),
    (",index_error", "Test index error"),
    (",key_error", "Test key error"),
    (",permission_error", "Test permission error"),
    (",type_error", "Test type error"),
    (",value_error", "Test value error"),
    
    # firstseen.py > FirstSeen
    (",firstseen <@user>", "Check when user was first seen"),
    (",setfirstseen <@user>", "Set first seen date for user"),
    
    # gambletickets.py > GambleSystem
    (",deposit <amount>", "Deposit currency into gambling system"),
    ("/ticket", "Create a support ticket"),
    (",withdraw <amount>", "Withdraw currency from gambling system"),
    
    # heartbeat.py > HeartbeatCog
    (",starthb", "Start heartbeat monitoring"),
    (",stophb", "Stop heartbeat monitoring"),
    
    # housetotal.py > HouseProfits
    (",houseprofits", "Display house profit statistics"),
    
    # devlist.py > InfoCog
    (",devlist", "List all available commands"),
    
    # invite.py > InviteCommand
    (",invite", "Get bot invite link"),
    
    # levels.py > LevelSystem
    (",addlevel <@user> <amount>", "Add levels to user"),
    (",addspeciallevel <@user> <level>", "Add special level to user"),
    (",alllevels", "Display all user levels"),
    (",assignspecial <@user> <level>", "Assign special level to user"),
    (",level <@user>", "Check user's level"),
    (",levels", "Display level leaderboard"),
    (",removespecial <@user>", "Remove special level from user"),
    (",showspecials", "Show all special levels"),
    
    # links.py > LinksCog
    (",links", "Display bot links"),
    
    # list.py > ListCog
    (",list", "Display this command list"),
    
    # logs.py > LogManager
    (",clearoldlogs", "Clear old log files"),
    (",logstatus", "Check logging status"),
    (",searchlog <query>", "Search through log files"),
    (",setstatuschannel <#channel>", "Set status update channel"),
    
    # maintenance.py > Maintenance
    (",maintenance", "Toggle maintenance mode"),
    (",resetname", "Reset bot name"),
    
    # deepseamerchfuture.py > MerchantUpdater
    (",stockupdate", "Update merchant stock information"),
    
    # ServerMessageReader.py > MessageReader
    (",messages", "Read server messages"),
    
    # mp3.py > Mp3
    (",mp3 <filename>", "Play MP3 file"),
    (",mp3list", "List available MP3 files"),
    (",stop", "Stop audio playback"),
    
    # volume.py > MusicCommands
    (",volume <1-100>", "Set bot volume"),
    
    # notificationalerts.py > NotificationSystem
    (",clearnotification", "Clear notifications"),
    (",inspect_embed", "Inspect embed structure"),
    (",notification", "Send notification"),
    (",setnotification", "Set up notifications"),
    
    # ownertest.py > OwnerTest
    (",testowner", "Test owner permissions"),
    (",whoowner", "Display bot owner"),
    
    # ely.py > PriceChecker
    (",recent", "Check recent RS3 item prices"),
    
    # profile.py > Profile
    (",profile <@user>", "Display user profile"),
    
    # react.py > ReactionCog
    (",react <emoji>", "Add reaction to message"),
    
    # rolecmds.py > RoleCmds
    (",addrole <@user> <@role>", "Add role to user"),
    (",removerole <@user> <@role>", "Remove role from user"),
    (",role <@user> <@role>", "Toggle role for user"),
    (",roles", "List server roles"),
    
    # viewroles.py > RoleViewer
    (",myaccess", "View your access permissions"),
    (",viewroles", "View all server roles"),
    
    # security.py > SecurityCamera
    (",reset_camera", "Reset security camera"),
    
    # ServerInfo.py > ServerInfo
    (",channellist", "List all server channels"),
    (",serverlist", "List all servers bot is in"),
    
    # Invitation.py > ServerInvite
    (",checkinvites", "Check server invites"),
    (",inviteserver", "Create server invite"),
    
    # leaveserver.py > ServerManagement
    (",leaveserver", "Leave current server"),
    
    # servermembers.py > ServerMembers
    (",servermembers", "List server members"),
    
    # servervoice.py > ServerVoiceJoin
    (",leavevc", "Leave voice channel"),
    (",serverjoin", "Join server voice channel"),
    (",voiceinfo", "Display voice channel info"),
    
    # elyimage.py > SetImage
    (",setimage", "Set profile image"),
    
    # stalk.py > Stalk
    (",stalk <@user>", "Stalk specified user"),
    (",stalkstatus", "Check stalking status"),
    (",stopstalk", "Stop stalking user"),
    
    # botstats.py > Statistics
    (",botstats", "Display bot statistics"),
    (",resetuptime", "Reset uptime counter"),
    
    # statuscmds.py > StatusCommands
    (",dnd", "Set bot status to Do Not Disturb"),
    (",offline", "Set bot status to Offline"),
    (",online", "Set bot status to Online"),
    (",resetstatus", "Reset bot status"),
    (",setstatus <type> <status>", "Set custom bot status"),
    
    # sync.py > Sync
    (",sync", "Sync slash commands"),
    
    # syncguild.py > SyncGuild
    (",clearcache", "Clear guild cache"),
    (",syncguild", "Sync guild data"),
    
    # sysevents.py > SystemEvents
    (",testsys", "Test system events"),
    
    # sysinfo.py > SystemMonitor
    (",sysinfo", "Display system information"),
    
    # tts.py > TextToSpeech
    (",tts <text>", "Text to speech in voice channel"),
    
    # timeout.py > Timeout
    (",timeout <@user> <duration> <reason>", "Timeout a user"),
    (",untimeout <@user>", "Remove timeout from user"),
    
    # deepseamerch.py > TravellingMerchant
    (",addchannel", "Add channel to merchant notifications"),
    (",listemoji", "List available emojis"),
    (",listsubscribed", "List subscribed channels"),
    (",merch", "Check travelling merchant"),
    (",merchusers", "List merchant subscribers"),
    (",sendmerch", "Send merchant update"),
    (",stock", "Check merchant stock"),
    (",testmerchant", "Test merchant functionality"),
    (",unaddchannel", "Remove channel from merchant notifications"),
    
    # ttv.py > Twitch
    (",ttv", "Twitch command"),
    (",ttvlist", "List Twitch streams"),
    (",ttvsort", "Sort Twitch streams"),
    
    # twitchbot.py > TwitchCog
    (",autostate", "Toggle auto state updates"),
    (",startauto", "Start automatic updates"),
    (",stopauto", "Stop automatic updates"),
    (",twitchconfig", "Configure Twitch settings"),
    
    # updateely.py > UpdateEly
    (",testdaily", "Test daily update"),
    (",updateely", "Update Ely data"),
    
    # uptime.py > Uptime
    (",uptime", "Display bot uptime"),
    
    # usercmds.py > UserCommands
    (",afk", "Toggle AFK status"),
    (",avatar <@user>", "Display user's avatar"),
    (",names <@user>", "Get old nicknames of user"),
    (",nickname <name>", "Set your nickname"),
    (",user <@user>", "Display user information"),
    
    # vip.py > VIPSystem
    (",vip", "VIP system commands"),
    
    # voiceofseren.py > VoSCog
    (",addvos", "Add Voice of Seren"),
    (",forcevos", "Force Voice of Seren update"),
    (",removevos", "Remove Voice of Seren"),
    (",test_vos", "Test Voice of Seren"),
    (",vos", "Check Voice of Seren"),
    
    # voicecmds.py > VoiceCommands
    (",deafen <@user>", "Deafen user in voice channel"),
    (",disconnect <@user>", "Disconnect user from voice channel"),
    (",drag <@user>", "Move user to your voice channel"),
    (",gather <#channel>", "Move all users to specified voice channel"),
    (",join <channel>", "Join voice channel"),
    (",mute <@user>", "Mute user in voice channel"),
    
    # webstats.py > WebStatsReporter
    (",teststats", "Test web statistics reporting"),
    
    # welcome.py > Welcome
    (",welcome", "Welcome message settings"),
    
    # youtubecmds.py > YouTubeCommands
    (",clearq", "Clear YouTube queue"),
    (",leave", "Leave voice channel"),
    (",play <URL/Search>", "Play YouTube music"),
    (",q", "Show YouTube queue"),
    
    # Slash Commands
    ("/setup", "Bot setup info (This is the only /slash command)"),
]



per_page = 5

class ListCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['help'])
    async def list(self, ctx):
        await ctx.message.delete()

        cog_chunks = [commands_list[i:i+per_page] for i in range(0, len(commands_list), per_page)]
        max_pages = len(cog_chunks)

        class CommandListView(discord.ui.View):
            def __init__(self, ctx, cog_chunks):
                super().__init__(timeout=30.0)
                self.ctx = ctx
                self.cog_chunks = cog_chunks
                self.current_page = 0
                self.message = None

            async def on_timeout(self):
                if self.message:
                    await self.message.delete()

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if interaction.user != self.ctx.author:
                    return
                self.current_page = max(0, self.current_page - 1)
                await self.update_embed()

            @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if interaction.user != self.ctx.author:
                    return
                self.current_page = min(max_pages - 1, self.current_page + 1)
                await self.update_embed()

            @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
            async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if interaction.user != self.ctx.author:
                    return
                await self.message.delete()
                self.stop()

            async def update_embed(self):
                embed = discord.Embed(title=f"Available Commands (Page {self.current_page+1})", color=discord.Color.dark_red())
                for command, description in self.cog_chunks[self.current_page]:
                    embed.add_field(name=command, value=description, inline=False)
                embed.set_footer(text=f"Page {self.current_page+1}/{max_pages}")
                self.previous.disabled = self.current_page == 0
                self.next.disabled = self.current_page == max_pages - 1
                if self.message:
                    await self.message.edit(embed=embed, view=self)
                else:
                    self.message = await self.ctx.send(embed=embed, view=self)

        view = CommandListView(ctx, cog_chunks)
        await view.update_embed()
        await view.wait()

async def setup(bot):
    await bot.add_cog(ListCog(bot))