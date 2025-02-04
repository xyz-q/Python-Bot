import discord
from discord.ext import commands
import json
import asyncio
import typing

json_file_path = ".json/mocked_users.json"

class ConfirmPurge(discord.ui.View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

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
    @commands.is_owner()
    async def purge(self, ctx, limit: int = 10, *, channel: typing.Optional[discord.TextChannel] = None):
        if limit <= 0:
            await ctx.send("Please specify a positive number for the limit.")
            return

        if limit > 300:
            await ctx.send("Limit cannot exceed 300.")
            return

        if channel is None:
            channel = ctx.channel

        class ConfirmPurge(discord.ui.View):
            def __init__(self, timeout=30):
                super().__init__(timeout=timeout)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                await interaction.response.defer()

        # Create confirmation view
        view = ConfirmPurge()
        
        # Show different messages based on whether purging current or different channel
        if channel == ctx.channel:
            confirm_text = f"Are you sure you want to purge {limit} messages from this channel?"
        else:
            confirm_text = f"Are you sure you want to purge {limit} messages from {channel.mention}?"
        
        confirm_msg = await ctx.send(confirm_text, view=view)

        # Wait for the user to interact with buttons
        await view.wait()
        
        # If user didn't respond in time
        if view.value is None:
            await confirm_msg.edit(content="Purge timed out.", view=None)
            return
        
        # If user cancelled
        if not view.value:
            await confirm_msg.edit(content="Purge cancelled.", view=None)
            return

        # If confirmed, proceed with purge
        try:
            # Delete confirmation message first
            await confirm_msg.delete()
            
            # Add status message in the channel where purge is happening
            status_msg = await channel.send(f"🧹 Cleaning {limit} messages...")
            
            # Delete messages in one bulk operation
            deleted = await channel.purge(
                limit=limit + 1,  # Add 1 to include the command message if in same channel
                check=lambda m: m.id != status_msg.id
            )

            # Update status message and delete after delay
            completion_msg = f"✨ Successfully purged {len(deleted)} messages!"
            await status_msg.edit(content=completion_msg)
            
            # If purging different channel, also send notification in command channel
            if channel != ctx.channel:
                notify_msg = await ctx.send(f"✨ Successfully purged {len(deleted)} messages from {channel.mention}!")
                await asyncio.sleep(3)
                await notify_msg.delete()
            
            await asyncio.sleep(3)
            await status_msg.delete()

        except discord.HTTPException as e:
            error_msg = f"An error occurred while purging messages: {e}"
            await ctx.send(error_msg)



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        await self.mock_message(message)

async def setup(bot):
    await bot.add_cog(ChatCommands(bot))
