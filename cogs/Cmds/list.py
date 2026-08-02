from discord.ext import commands
import discord
import asyncio

commands_list = [
    (",accept", "Accept a trade or transaction"),
    (",add <amount>", "Add currency to account"),
    (",add_drops", "Interactive command to add boss drops"),
    (",addgz", "Add gz entry"),
    (",addlevel <@user> <amount>", "Add levels to user"),
    (",addrole <@user> <@role>", "Add role to user"),
    (",addspeciallevel <@user> <level>", "Add special level to user"),
    (",addvos", "Add Voice of Seren"),
    (",afk", "Toggle AFK status"),
    (",ai", "AI command"),
    (",alerts", "View your RS3 price alerts"),
    (",alchables", "Displays best high alch items"),
    (",alllevels", "Display all user levels"),
    (",another_task", "Another task command"),
    (",assignspecial", "Assign special level to user"),
    (",audit <#>", "Displays audit logs"),
    (",autodelete", "Toggle autodelete"),
    (",autostate", "Toggle Twitch auto state updates"),
    (",avatar <@user>", "Display user's avatar"),
    (",balance", "Check your balance"),
    (",balancelist", "List all user balances"),
    (",ban <@member> <reason> <delete_messages>", "Ban a member"),
    (",blackjack <amount>", "Play blackjack"),
    (",blacklist <@user>", "Add or remove user from blacklist"),
    (",botstats", "Display bot statistics"),
    (",bugreport", "Open the bug report form"),
    (",channellist", "List all server channels"),
    (",checkhtml <url> <search_term>", "Check HTML structure"),
    (",checkinvites", "Check server invites"),
    (",checkpublish", "Check publishing configuration"),
    (",clearnotification", "Clear notifications"),
    (",clearcurrency", "Clear all currency data"),
    (",clearoldlogs", "Clear old log files"),
    (",clearq", "Clear YouTube queue"),
    (",cleartransactions", "Clear transaction history"),
    (",clearrs3drops", "Clear RS3 drops"),
    (",clearcache", "Clear guild cache"),
    (",cleanup_status", "Check cleanup task status"),
    (",coinflip", "Flip a coin"),
    (",compare", "Compare actual commands with hardcoded list"),
    (",cs2clear", "Clear CS2 update ID"),
    (",cs2notify", "Toggle CS2 update notifications"),
    (",cs2status", "Check CS2 tracking status"),
    (",cs2updates", "Get latest CS2 patch notes"),
    (",deafen <@user>", "Deafen user"),
    (",deploy", "Deploy command"),
    (",deposit <amount>", "Deposit currency"),
    (",devlist", "List all available commands"),
    (",disconnect <@user>", "Disconnect user from voice"),
    (",dm <@user> <message>", "Send DM"),
    (",dms <@user>", "Show bot's DMs with a user"),
    (",dnd", "Set bot status to Do Not Disturb"),
    (",downtime", "Check bot downtime"),
    (",drag <@user>", "Move user to your voice channel"),
    (",emoji", "Get emoji details"),
    (",emojiadd <link>", "Create emoji"),
    (",emojiremove <name>", "Delete emoji"),
    (",emojis", "List server emojis"),
    (",firstseen <@user>", "Check when user was first seen"),
    (",flower", "Flower poker"),
    (",forcevos", "Force Voice of Seren update"),
    (",gather <#channel>", "Move all users to voice channel"),
    (",hello", "Hello world"),
    (",housestats", "Display house gambling stats"),
    (",houseprofits", "Display house profit statistics"),
    (",inspect_embed", "Inspect embed structure"),
    (",invite", "Get bot invite link"),
    (",inviteserver", "Create server invite"),
    (",join <channel>", "Join voice channel"),
    (",kick <@user(s)> <reason>", "Kick user(s)"),
    (",kill", "Kill bot"),
    (",leave", "Leave voice channel"),
    (",leaveserver", "Leave current server"),
    (",leavevc", "Leave voice channel"),
    (",level <@user>", "Check user level"),
    (",levels", "Display level leaderboard"),
    (",limits", "Show gambling limits"),
    (",links", "Display bot links"),
    (",list", "Display command list"),
    (",listcogs", "List all cogs"),
    (",logstatus", "Check logging status"),
    (",long_task", "Long running task"),
    (",maintenance", "Toggle maintenance mode"),
    (",messages", "Read server messages"),
    (",mock <@user>", "Toggle mocking"),
    (",mp3 <filename>", "Play MP3"),
    (",mp3list", "List MP3 files"),
    (",mystats", "Display your command usage stats"),
    (",myaccess", "View your access permissions"),
    (",myalerts", "Display your alerts"),
    (",mute <@user>", "Mute user in voice channel"),
    (",names <@user>", "Get old nicknames"),
    (",nickname <name>", "Set your nickname"),
    (",notification", "Send notification"),
    (",notify <item> <price> <h/l>", "Set RS3 price alert"),
    (",offline", "Set bot offline"),
    (",online", "Set bot online"),
    (",osrsclog", "OSRS clog"),
    (",osrsclogclear", "Clear OSRS clog"),
    (",osrsclogview", "View OSRS clog"),
    (",ping", "Ping command"),
    (",play <URL/Search>", "Play YouTube music"),
    (",profile <@user>", "Display user profile"),
    (",publish", "Start auto-publishing"),
    (",publishing", "Check auto-publishing channels"),
    (",purge <limit> <#channel>", "Delete messages"),
    (",pvpflip", "PvP coin flip"),
    (",q", "Show YouTube queue"),
    (",react <emoji>", "Add reaction"),
    (",recent", "Check recent RS3 prices"),
    (",removerole <@user> <@role>", "Remove role"),
    (",remove <amount>", "Remove currency"),
    (",removealert <item>", "Remove RS3 alert"),
    (",removegz", "Remove gz entry"),
    (",removespecial <@user>", "Remove special level"),
    (",removevos", "Remove Voice of Seren"),
    (",reset_camera", "Reset security camera"),
    (",resetname", "Reset bot name"),
    (",resetstatus", "Reset bot status"),
    (",resetstats", "Reset gambling stats"),
    (",resetuptime", "Reset uptime counter"),
    (",role <@user> <@role>", "Toggle role"),
    (",roles", "List server roles"),
    (",say <#channel> 'TEXT'", "Bot says text"),
    (",searchlog <query>", "Search log files"),
    (",serverjoin", "Join server voice channel"),
    (",serverlist", "List servers"),
    (",servermembers", "List server members"),
    (",setbalance <amount>", "Set balance"),
    (",set_cleanup_interval <minutes>", "Set cleanup interval"),
    (",setfirstseen <@user>", "Set first seen date"),
    (",setimage", "Set profile image"),
    (",setnotification", "Set up notifications"),
    (",setstatus <type> <status>", "Set custom bot status"),
    (",showspecials", "Show all special levels"),
    (",simulate <boss_name> <kill_count>", "Simulate boss kills"),
    (",slots", "Slot machine"),
    (",stalk <@user>", "Stalk user"),
    (",stalkstatus", "Check stalking status"),
    (",staking", "Staking gambling game"),
    (",startauto", "Start Twitch auto updates"),
    (",starthb", "Start heartbeat"),
    (",stats", "Display gambling stats"),
    (",stockupdate", "Update merchant stock"),
    (",stop", "Stop audio"),
    (",stopauto", "Stop Twitch auto updates"),
    (",stopstalk", "Stop stalking"),
    (",stophb", "Stop heartbeat"),
    (",stoppublish", "Stop auto-publishing"),
    (",sysinfo", "Display system info"),
    (",sync", "Sync slash commands"),
    (",syncguild", "Sync guild data"),
    (",timeout <@user> <duration> <reason>", "Timeout user"),
    (",toggle_cleanup", "Toggle cleanup task"),
    (",transactions", "View transaction history"),
    (",transfer <@user> <amount>", "Transfer currency"),
    (",tts <text>", "Text to speech"),
    (",ttv", "Twitch command"),
    (",ttvlist", "List Twitch streams"),
    (",ttvsort", "Sort Twitch streams"),
    (",twitchconfig", "Configure Twitch settings"),
    (",untimeout <@user>", "Remove timeout"),
    (",updateely", "Update Ely data"),
    (",uptime", "Display uptime"),
    (",user <@user>", "Display user info"),
    (",vault", "Access vault"),
    (",viewbugs", "View bug reports"),
    (",viewroles", "View all roles"),
    (",vip", "VIP system commands"),
    (",voiceinfo", "Display voice channel info"),
    (",vos", "Check Voice of Seren"),
    (",volume <1-100>", "Set bot volume"),
    (",welcome", "Welcome message settings"),
    ("/ticket", "Create support ticket"),
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