from discord.ext import commands
import discord
import asyncio

commands_list = [
    ("/setup", "Bot setup info (This is the only /slash command)"),
    (",autodelete", "Toggles the bot's autodelete function"),
    (",avatar <@user>", "Gets user's avatar"),
    (",afk", "Toggle your status of AFK"),
    (",clearq", "Removes all music from the queue"),
    (",dnd", "Toggles the bot between DnD and Idle Mode"),
    (",dm <target> <message>", "Sends a message to target user"),
    (",dms <target>", "Shows the bot's dms with a user"),
    (",disconnect <@user>", "Disconnect user from a voice channel"),
    (",drag <@user>", "Move a user to a voice channel"),
    (",emojiadd <link>", "Creates an emoji"),
    (",emoji", "Gives details of an emoji"),
    (",emojiremove <name>", "Deletes an emoji"),
    (",deafen <@user>", "Deafens the target user, if none is specified it deafens the bot"),
    (",gather <#channel>", "Moves all users into the voice channel that you are in or the channel specified."),
    (",join <channel-name> (optional)", "Joins the channel you're in, or if specified it joins the channel name"),
    (",jail <@user>", "Assigns the user to the '.jail' role"),
    (",kill", "KILLS THE BOT [restricted command]"),
    (",kick <@user(s)> {reason}", "Kicks the user(s) from the server"),
    (",leave", "Leaves the channel the bot is in"),
    (",mock <@user>", "Mocks target user(s)"),
    (",mute <@user>", "Mutes target user"),
    (",mp3list", "Shows a list of mp3s in the file"),
    (",names <@user>", "Gets the old nicknames of a user"),
    (",online", "Sets bot status as 'Online'"),
    (",offline", "Sets bot status as 'Offline'"),
    (",pause", "Halts audio playback"),
    (",play <URL/Search>", "Plays youtube music"),
    (",mp3 <mp3>", "Plays Target MP3"),
    ("/price", "Check the price of a CS2 skin on CSFloat"),
    (",ping", "Ping command - Test if the bot is responsive- displays the latency from the bot to the server"),
    (",purge <#channel/number> <number>", "Deletes messages in #channel if specified, default is 100"),
    (",q", "Shows the music queue"),
    (",release <@user>", "Releases the user from the '.jail' role"),
    (",resetstatus", "Resets the bot's status"),
    (",resume", "Continues audio playback"),
    (",stalk <@user>", "Stalks the specified user"),
    (",stopstalk", "Stops stalking selected user"),
    (",setstatus <activity-type> <status>", "Sets the bot's status"),
    (",skip", "Skips a song in queue"),
    (",say <#channel> 'TEXT'", "Makes the bot chat the desired text in specified channel"),
    ("/ticket", "Creates a ticket"),
    (",user <@user>", "Displays info on user"),
    ("[WIP],volume <1-100>", "Sets the bot's volume"),
    
]

per_page = 5

class list(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_list(self, ctx, page, message=None):
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        commands_page = commands_list[start_index:end_index]
        embed = discord.Embed(title=f"Available Commands (Page {page})", color=discord.Color.dark_red())
        for command, description in commands_page:
            embed.add_field(name=command, value=description, inline=False)
        embed.set_footer(text=f"Page {page}/{(len(commands_list) - 1) // per_page + 1}")
        if message:
            await message.edit(embed=embed)
        else:
            message = await ctx.send(embed=embed)
            await message.add_reaction('⬅️')
            await message.add_reaction('➡️')
            await message.add_reaction('❌') 
        return message

    @commands.command(aliases=['help'])
    async def list(self, ctx, page: int = 1):
        await ctx.message.delete()
        message = await self.send_list(ctx, page)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️', '❌'] 
        try:
            while True:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)

                if str(reaction.emoji) == '⬅️':
                    page = max(1, page - 1)
                elif str(reaction.emoji) == '➡️':
                    page = min((len(commands_list) - 1) // per_page + 1, page + 1)
                elif str(reaction.emoji) == '❌': 
                    await message.delete() 
                    return

                await self.send_list(ctx, page, message=message)
                await message.remove_reaction(reaction.emoji, user)

        except asyncio.TimeoutError:
            await message.delete()  

async def setup(bot):
    await bot.add_cog(list(bot))