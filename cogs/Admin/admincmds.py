import discord
from discord.ext import commands
import asyncio
import json
import sys 

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_delete_enabled = False
        self.AUTO_DELETE_FILE = "auto_delete.json"
        self.ORIGINAL_NAME = "xyz"
        try:
            with open(self.AUTO_DELETE_FILE, "r") as f:
                self.auto_delete_enabled = json.load(f)
        except FileNotFoundError:
            self.auto_delete_enabled = False

    def save_auto_delete_status(self):
        with open(self.AUTO_DELETE_FILE, "w") as f:
            json.dump(self.auto_delete_enabled, f)

    @commands.command()
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("I don't have permission to kick members.")
            return

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for member in members:
            try:
                embed = discord.Embed(
                    title="⚠️ Kick Notification",
                    description=f"You have been kicked from {ctx.guild.name}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Kicked By", value=f"{ctx.author.name}", inline=False)
                embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
                embed.add_field(name="Date & Time", value=current_time, inline=False)

                try:
                    dm_channel = await member.create_dm()
                    await dm_channel.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send(f"Could not DM {member.mention} about their kick.")
                except Exception as e:
                    await ctx.send(f"Error sending DM to {member.mention}: {str(e)}")

                await member.kick(reason=reason)
                await ctx.send(f"{member.mention} has been kicked. Reason: {reason if reason else 'No reason provided'}")

            except discord.Forbidden:
                await ctx.send(f"I don't have permission to kick {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to kick {member.mention}.")



    @commands.command()
    async def ping(self, ctx):
        bot_latency = round(self.bot.latency * 1000) 
        embed = discord.Embed(title=" ", description=f"Pong! 🏓\nBot latency: {bot_latency} ms", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello world!")

    @commands.command()
    async def kill2(self, ctx):
        if ctx.author.id == 110927272210354176: 
            warning_message = await ctx.send(":warning: Are you sure you want to TERMINATE the bot? This action cannot be undone.")
            await warning_message.add_reaction("🔴")  
            await warning_message.add_reaction("🟢")  

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["🔴", "🟢"]
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=10, check=check)
                if str(reaction.emoji) == "🔴":
                    await warning_message.clear_reactions()  
                    await warning_message.edit(content=" :orange_circle: Bot TERMINATION cancelled.")
                    print("Bot termination CANCELLED")
                elif str(reaction.emoji) == "🟢":
                    await warning_message.clear_reactions()  
                    await warning_message.edit(content=":warning: Bot instance(s) TERMINATED.")
                    print("\033[96m" + f"BOT HAS BEEN TERMINATED BY: {ctx.author.name} ({ctx.author.id})" + "\033[0m")
                    guild = self.bot.get_guild(1056994840925192252)  
                    channel = discord.utils.get(guild.text_channels, name="bot-status")
                    if channel:
                        await channel.send(":red_circle: xyz is now offline [Killed]")
                    sys.exit()
            except asyncio.TimeoutError:
                await warning_message.edit(content=":clock1:  Bot TERMINATION cancelled due to inactivity.")
                print("Bot termination CANCELLED from inactivity")
                await warning_message.clear_reactions()  
        else:
            await ctx.send(f":warning: [ERROR] {ctx.author.mention} is not permitted to operate this command.")
            print("\033[96m" + f"USER TRYING TO KILL BOT: {ctx.author.name} ({ctx.author.id})" + "\033[0m")

 
    @commands.command()
    async def autodelete(self, ctx):
        self.auto_delete_enabled = not self.auto_delete_enabled
        await ctx.send(f"Auto-delete commands {'enabled' if self.auto_delete_enabled else 'disabled'}.")
        self.save_auto_delete_status()

    @commands.Cog.listener()
    async def on_command(self, ctx):
       
        if self.auto_delete_enabled:
            try:
                await ctx.message.delete()
                bot_response = await ctx.send(ctx.message.content)
                await asyncio.sleep(0.5)
                async for message in ctx.channel.history(after=ctx.message.created_at):
                    if message.author == self.bot.user:
                        await message.delete()
                    else:
                        break  
            except discord.Forbidden:
                print("Bot doesn't have permission to delete messages.")

        await self.update_bot_username(ctx)

    async def update_bot_username(self, ctx):
        """Update the bot's nickname dynamically for each guild."""
        for guild in self.bot.guilds:
            try:
                # Get the current nickname or fall back to the default username
                current_nickname = guild.me.nick  # Current nickname
                if current_nickname and current_nickname.startswith("🗑"):
                    # Extract the name after the emoji (remove it)
                    original_name = current_nickname[2:].strip()
                else:
                    # Use the current nickname or default username as the original name
                    original_name = guild.me.nick or guild.me.name
                
                # Build the new nickname based on auto_delete_enabled
                if self.auto_delete_enabled:
                    new_nickname = f"🗑 {original_name}"
                else:
                    new_nickname = original_name

                # Ensure the nickname doesn't exceed 32 characters
                if len(new_nickname) > 32:
                    new_nickname = new_nickname[:32]

                # Avoid redundant updates
                if current_nickname != new_nickname:
                    await guild.me.edit(nick=new_nickname)
            except discord.HTTPException as e:
                print(f"Failed to update bot's nickname in guild {guild.name}: {e}")
    @commands.command()
    @commands.is_owner()
    async def audit(self, ctx, limit: int = 10):
        try:
            # Convert audit logs to a list using list comprehension
            audit_log = [entry async for entry in ctx.guild.audit_logs(limit=limit)]
            
            if not audit_log:
                await ctx.send("No audit log entries found.")
                return
                
            embed = discord.Embed(title="Moderation Audit Log", color=discord.Color.blurple())
            
            for entry in audit_log:
                try:
                    action_type = entry.action
                    target = entry.target
                    responsible_user = entry.user
                    reason = entry.reason or "No reason provided"
                    
                    target_text = target.mention if target else "Unknown Target"
                    
                    embed.add_field(
                        name=f"{action_type.name}", 
                        value=f"Target: {target_text}\nResponsible: {responsible_user.mention}\nReason: {reason}", 
                        inline=False
                    )
                except AttributeError as e:
                    print(f"Error processing entry: {e}")
                    continue

            # Create the X button
            delete_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Close")
            
            # Create a view and add the button
            view = discord.ui.View(timeout=60)
            view.add_item(delete_button)

            # Button callback
            async def delete_callback(interaction):
                if interaction.user.id == ctx.author.id:
                    await interaction.message.delete()
                else:
                    await interaction.response.send_message("You can't delete this message!", ephemeral=True)

            delete_button.callback = delete_callback
            
            # Send the message with the view
            message = await ctx.send(embed=embed, view=view)
            
            # Delete after 60 seconds
            await asyncio.sleep(60)
            try:
                await message.delete()
            except discord.NotFound:
                pass  # Message was already deleted manually

        except discord.Forbidden:
            await ctx.send("I don't have permission to view the audit log.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error in audit command: {e}")





async  def setup(bot):
    await bot.add_cog(AdminCommands(bot))
