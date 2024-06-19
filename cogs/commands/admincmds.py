import discord
from discord.ext import commands
import asyncio
import json

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_delete_enabled = False
        self.AUTO_DELETE_FILE = "auto_delete.json"
        self.ORIGINAL_NAME = "xyz"

        # Load auto-delete status from file
        try:
            with open(self.AUTO_DELETE_FILE, "r") as f:
                self.auto_delete_enabled = json.load(f)
        except FileNotFoundError:
            self.auto_delete_enabled = False

    def save_auto_delete_status(self):
        # Save auto-delete status to file
        with open(self.AUTO_DELETE_FILE, "w") as f:
            json.dump(self.auto_delete_enabled, f)

    # Command to kick members
    @commands.command()
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        # Check if the bot has permission to kick members
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("I don't have permission to kick members.")
            return

        # Kick each member
        for member in members:
            try:
                await member.kick(reason=reason)
                if reason:
                    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
                else:
                    await ctx.send(f"{member.mention} has been kicked.")
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to kick {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to kick {member.mention}.")

    # Command: Ping (test command)
    @commands.command()
    async def ping(self, ctx):
        # Get the bot's latency to the server
        bot_latency = round(self.bot.latency * 1000)  # Latency in milliseconds

        # Create an embed
        embed = discord.Embed(title=" ", description=f"Pong! 🏓\nBot latency: {bot_latency} ms", color=discord.Color.blurple())

        # Send the embed
        await ctx.send(embed=embed)

    # Command: Hello (example command)
    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello world!")

    # KILL COMMAND
    @commands.command()
    async def kill(self, ctx):
        # Check if the user invoking the command is the specified user
        if ctx.author.id == 110927272210354176:  # Replace with the user ID of .zxpq
            warning_message = await ctx.send(":warning: Are you sure you want to TERMINATE the bot? This action cannot be undone.")
            await warning_message.add_reaction("🔴")  # Red button
            await warning_message.add_reaction("🟢")  # Green button

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["🔴", "🟢"]

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=10, check=check)
                if str(reaction.emoji) == "🔴":
                    await warning_message.clear_reactions()  # Remove reactions
                    await warning_message.edit(content=" :orange_circle: Bot TERMINATION cancelled.")
                elif str(reaction.emoji) == "🟢":
                    await warning_message.clear_reactions()  # Remove reactions
                    await warning_message.edit(content=":warning: Bot instance(s) TERMINATED.")
                    print("\033[96m" + f"BOT HAS BEEN TERMINATED BY: {ctx.author.name} ({ctx.author.id})" + "\033[0m")
                    guild = self.bot.get_guild(1056994840925192252)  # Replace YOUR_GUILD_ID with your guild's ID
                    channel = discord.utils.get(guild.text_channels, name="bot-status")

                    if channel:
                        # Send a message to the "bot-status" text channel indicating that the bot is going offline
                        await channel.send(":red_circle: xyz is now offline [Killed]")
                    await self.bot.close()
            except asyncio.TimeoutError:
                await warning_message.edit(content=":clock1:  Bot TERMINATION cancelled due to inactivity.")
                await warning_message.clear_reactions()  # Remove reactions
        else:
            await ctx.send(f":warning: [ERROR] {ctx.author.mention} is not permitted to operate this command.")
            print("\033[96m" + f"USER TRYING TO KILL BOT: {ctx.author.name} ({ctx.author.id})" + "\033[0m")

    # Command: Auto delete command
    @commands.command()
    async def autodelete(self, ctx):
        self.auto_delete_enabled = not self.auto_delete_enabled
        await ctx.send(f"Auto-delete commands {'enabled' if self.auto_delete_enabled else 'disabled'}.")

        # Save auto-delete status to file
        self.save_auto_delete_status()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Check if auto-delete is enabled
        if self.auto_delete_enabled:
            try:
                # Delete the command message
                await ctx.message.delete()

                # Execute the command and get the bot's response
                bot_response = await ctx.send(ctx.message.content)

                # Delay for 1/2 second
                await asyncio.sleep(0.5)

                # Get bot's messages sent after the command
                async for message in ctx.channel.history(after=ctx.message.created_at):
                    if message.author == self.bot.user:
                        await message.delete()
                    else:
                        break  # Exit loop if a non-bot message is encountered
            except discord.Forbidden:
                print("Bot doesn't have permission to delete messages.")

        # Update bot's username
        await self.update_bot_username(ctx)

    async def update_bot_username(self, ctx):
        # Change bot's nickname based on auto-delete setting
        new_nickname = f" 🗑️ {self.ORIGINAL_NAME} ️" if self.auto_delete_enabled else self.ORIGINAL_NAME

        try:
            for guild in self.bot.guilds:
                await guild.me.edit(nick=new_nickname)
        except discord.HTTPException as e:
            print(f"Failed to update bot's nickname: {e}")

async  def setup(bot):
    await bot.add_cog(AdminCommands(bot))
