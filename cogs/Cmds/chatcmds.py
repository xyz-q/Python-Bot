import discord
from discord.ext import commands
import json
import asyncio
import typing

json_file_path = "mocked_users.json"

class ChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        try:
            with open(json_file_path, 'r') as file:
                self.mocked_users = json.load(file)
        except FileNotFoundError:
            self.mocked_users = {}

    def save_mocked_users(self):
        with open(json_file_path, 'w') as file:
            json.dump(self.mocked_users, file)

    async def mock_message(self, message):
        if message.content.startswith(','): 
            return False

        user_id = str(message.author.id)
        if user_id in self.mocked_users and self.mocked_users[user_id]:
            mocked_text = ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content))
            await message.channel.send(mocked_text)
            return True
        return False

    @commands.command()
    async def mock(self, ctx, target: discord.Member = None):
        if target is None:
            await ctx.send("Please mention a user to toggle mocking.")
            return

        if target.bot and target.name == "xyz": 
            await ctx.send("Cannot toggle mocking for bot.")
            return

        user_id = str(target.id)
        self.mocked_users[user_id] = not self.mocked_users.get(user_id, False)
        self.save_mocked_users() 

        if self.mocked_users[user_id]:
            await ctx.send(f"Mocking enabled for {target.display_name}.")
        else:
            await ctx.send(f"Mocking disabled for {target.display_name}.")


    @commands.command()
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        print(f"\033[95mUser: {ctx.author.name} ({ctx.author.id}) said: {message}\033[0m")
        await channel.send(message)

    @commands.command()
    async def purge(self, ctx, channel: typing.Optional[discord.TextChannel] = None, limit: int = 10):
        if limit <= 0:
            await ctx.send("Please specify a positive number for the limit.")
            return

        if limit > 300:
            await ctx.send("Limit cannot exceed 300.")
            return

        if channel is None:
            channel = ctx.channel

        limit += 1              

        try:
            def check(message):
                return True

            total_deleted = 0
            while total_deleted < limit:
                to_delete = min(limit - total_deleted, 5)
                deleted = await channel.purge(limit=to_delete, check=check)
                total_deleted += len(deleted)

                await asyncio.sleep(0.25)

            confirmation_msg = await ctx.send(f"Purged {total_deleted} message(s) from {channel.mention}.")
            await asyncio.sleep(3.5)
            await confirmation_msg.delete()

        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while purging messages: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        await self.mock_message(message)

async def setup(bot):
    await bot.add_cog(ChatCommands(bot))
