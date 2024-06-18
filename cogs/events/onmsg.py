import asyncio
import discord
from discord.ext import commands

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Respond to DMs with a message
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("hi there :D i can only process commands in a guild. /setup for more info")
            return

        # Delete messages in specific channel
        if message.channel.id == 1234310879072223292 and not message.author.bot:
            await message.delete()
            warning_msg = await message.channel.send(
                f'{message.author.mention}, sending messages in this channel is not allowed.')
            await asyncio.sleep(4)
            await warning_msg.delete()
            return

        # AFK user handling
        afk_users = self.bot.afk_users  # Assuming afk_users is a property of your bot
        mentioned_afk_users = [user_id for user_id in afk_users if
                               message.guild.get_member(int(user_id)) in message.mentions]

        if mentioned_afk_users:
            for user_id in mentioned_afk_users:
                reason = afk_users[user_id]
                user = message.guild.get_member(int(user_id))
                await message.channel.send(f"{user.mention} is currently AFK. Reason: {reason}")

        # Command handling
        if message.content.startswith(self.bot.command_prefix):

            if not message.content.startswith(self.bot.command_prefix + "list"):
                if message.channel.name != "admin-commands":
                    error_message = ":warning: Commands can only be used in the #admin-commands channel. [/setup]"
                    response = await message.channel.send(error_message)
                    print(f"\033[95m{message.author} Tried to activate command in another channel\033[0m")
                    await message.delete()
                    await asyncio.sleep(4)
                    await response.delete()
                    return

                trusted_role = discord.utils.get(message.guild.roles, name=self.bot.trusted_role_name)

                if trusted_role and trusted_role not in message.author.roles:
                    response = await message.channel.send(
                        f" :warning: [ERROR] {message.author.mention} is not permitted to operate commands.")
                    print(f"\033[95m{message.author} tried to use command '{message.content}' without trusted role\033[0m")
                    await message.delete()
                    await asyncio.sleep(4)
                    await response.delete()
                    return

        if not message.content.startswith(self.bot.command_prefix) and message.channel.name == "admin-commands":
            await message.delete()
            warning_msg = await message.channel.send(
                f'{message.author.mention}, you need to be using a command in this channel.')
            await asyncio.sleep(4)
            await warning_msg.delete()
            return

        await self.bot.process_commands(message)
        await self.mock_message(message)  # Assuming mock_message is defined somewhere

    async def mock_message(self, message):
        # Define your mock_message logic here
        pass

def setup(bot):
    bot.add_cog(OnMessage(bot))