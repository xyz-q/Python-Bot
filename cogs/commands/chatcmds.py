import discord
from discord.ext import commands
import json
import asyncio
import typing

# Path to your JSON file for mocked users
json_file_path = "mocked_users.json"

class ChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load mocked users data
        try:
            with open(json_file_path, 'r') as file:
                self.mocked_users = json.load(file)
        except FileNotFoundError:
            self.mocked_users = {}

    # Function to save mocked users data
    def save_mocked_users(self):
        with open(json_file_path, 'w') as file:
            json.dump(self.mocked_users, file)

    # Function to mock a message
    async def mock_message(self, message):
        if message.content.startswith(','):  # Skip mocking if the message contains the command invocation
            return False

        user_id = str(message.author.id)
        if user_id in self.mocked_users and self.mocked_users[user_id]:
            mocked_text = ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content))
            await message.channel.send(mocked_text)
            return True
        return False

    # Command: Mock command
    @commands.command()
    async def mock(self, ctx, target: discord.Member = None):
        if target is None:
            await ctx.send("Please mention a user to toggle mocking.")
            return

        if target.bot and target.name == "xyz":  # Replace "xyz" with your bot's name
            await ctx.send("Cannot toggle mocking for bot.")
            return

        # Toggle mocking for the specified user
        user_id = str(target.id)
        self.mocked_users[user_id] = not self.mocked_users.get(user_id, False)
        self.save_mocked_users()  # Save mocked users after toggling

        if self.mocked_users[user_id]:
            await ctx.send(f"Mocking enabled for {target.display_name}.")
        else:
            await ctx.send(f"Mocking disabled for {target.display_name}.")

    # Command : Say command
    @commands.command()
    async def say(self, ctx, channel: discord.TextChannel, *, message):
        # Print the user who sent the text and the text itself in purple
        print(f"\033[95mUser: {ctx.author.name} ({ctx.author.id}) said: {message}\033[0m")

        # Send the message to the specified channel
        await channel.send(message)

    # Command : Purge command to delete specified messages in specified channel
    @commands.command()
    async def purge(self, ctx, channel: typing.Optional[discord.TextChannel] = None, limit: int = 100):
        if limit <= 0:
            await ctx.send("Please specify a positive number for the limit.")
            return

        if limit > 300:
            await ctx.send("Limit cannot exceed 300.")
            return

        if channel is None:
            channel = ctx.channel

        try:
            # Define a check function to delete all messages in the channel
            def check(message):
                return True

            # Attempt to delete messages in batches of 5 until the limit is reached
            total_deleted = 0
            while total_deleted < limit:
                to_delete = min(limit - total_deleted, 5)
                deleted = await channel.purge(limit=to_delete, check=check)
                total_deleted += len(deleted)

                # Add a short delay between batches to prevent rate limits
                await asyncio.sleep(1)

            # Send the final result after completion
            confirmation_msg = await ctx.send(f"Purged {total_deleted} message(s) from {channel.mention}.")
            await asyncio.sleep(5)
            await confirmation_msg.delete()

        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while purging messages: {e}")

    # Event: on_message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:  # Ignore messages sent by the bot itself
            return

        await self.mock_message(message)

async def setup(bot):
    await bot.add_cog(ChatCommands(bot))
