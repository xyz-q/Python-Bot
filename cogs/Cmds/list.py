from discord.ext import commands
import discord
import asyncio

commands_list = [
    ("/setup", "Bot setup info (This is the only /slash command)"),
    (",autodelete", "Toggles the bot's autodelete function"),
    (",audit <#>", "Displays audit logs"),
    (",afk", "Toggle your status of AFK"),
    (",avatar <@user>", "Displays specified users avatar."),
    (",alert <item> <price> <h/l>", "Alerts the user if an item on RS3 goes past a certain threshold"),
    (",alerts", "Alerts the user if an item on RS3 goes past a certain threshold"),
    (",myalerts", "Displays user's alerts"),
    (",removealert <item>", "Removes an alert for specific item"),
    (",ban <reason> <delete message history (0-7)>", "Bans the user, showing who banned them and for what"),
    (",clearq", "Removes all music from the queue"),
    (",cogs", "Lists all cogs"),
    (",dnd", "Toggles the bot between DnD and Idle Mode"),
    (",dm <target> <message>", "Sends a message to target user"),
    (",dms <target>", "Shows the bot's dms with a user"),
    (",disconnect <@user>", "Disconnect user from a voice channel"),
    (",drag <@user>", "Move a user to a voice channel"),
    (",emojiadd <link>", "Creates an emoji"),
    (",emoji", "Gives details of an emoji"),
    (",emojiremove <name>", "Deletes an emoji"),
    (",deafen <@user>", "Deafens the target user, if none is specified it deafens the bot"),
    (",gather <#channel>", "Moves all users into the voice channel that you are in or the channel specified"),
    (",invite", "Gives the user a temporary invite link"),
    (",join <channel-name> (optional)", "Joins the channel you're in, or if specified it joins the channel name"),
    (",kill", "KILLS THE BOT [restricted command]"),
    (",kick <@user(s)> <reason>", "Kicks the user(s) from the server"),
    (",listcogs", "Lists all cogs"),
    (",links", "Displays my links"),  
    (",leave", "Leaves the channel the bot is in"),
    (",mock <@user>", "toggles the mocking of target user(s)"),
    (",mute <@user>", "Mutes target user"),
    (",mp3list", "Shows a list of mp3s in the file"),
    (",mp3 <mp3>", "Plays Target MP3"),
    (",names <@user>", "Gets the old nicknames of a user"),
    (",online", "Sets bot status as 'Online'"),
    (",offline", "Sets bot status as 'Offline'"),
    (",pc <item>", "Check the price of a RS3 skin"),
    (",pause", "Halts audio playback"),
    (",play <URL/Search>", "Plays youtube music"),
    ("/price", "Check the price of a CS2 skin on CSFloat"),
    (",ping", "Ping command - Test if the bot is responsive- displays the latency from the bot to the server"),
    (",purge <#channel/number> <number>", "Deletes messages in #channel if specified, default is 10"),
    (",q", "Shows the music queue"),
    (",role <@user> <@role>", "Add or remove a role from the user"),
    (",resetstatus", "Resets the bot's status"),
    (",resume", "Continues audio playback"),
    (",runtime", "Displays bot's uptime"),
    (",stalk <@user>", "Stalks the specified user"),
    (",stopstalk", "Stops stalking selected user"),
    (",setstatus <activity-type> <status>", "Sets the bot's status"),
    (",skip", "Skips a song in queue"),
    (",say <#channel> 'TEXT'", "Makes the bot chat the desired text in specified channel"),
    ("/ticket", "Creates a ticket"),
    (",timeout <@user> <duration> <reason>", "Times out a user, sending them a detailed message"),
    (",tts <text>", "Makes the bot do a text to speech in the voice channel if its in one"),
    (",tuck", "Puts users to bed"),
    (",user <@user>", "Displays info on user"),
    (",untimeout <@user>", "Removes a timeout from a user"),
    (",uptime", "Displays bot's uptime"),
    ("[WIP],volume <1-100>", "Sets the bot's volume"),
    
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