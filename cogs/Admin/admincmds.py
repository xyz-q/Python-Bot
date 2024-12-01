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
#############################################
    @commands.command()
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("I don't have permission to kick members.")
            return

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for member in members:
            try:
                # Create embed for DM
                embed = discord.Embed(
                    title="⚠️ Kick Notification",
                    description=f"You have been kicked from {ctx.guild.name}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Kicked By", value=f"{ctx.author.name}", inline=False)
                embed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
                embed.add_field(name="Date & Time", value=current_time, inline=False)

                # First, try to send DM
                try:
                    # Create a DM channel and send message BEFORE kicking
                    dm_channel = await member.create_dm()
                    await dm_channel.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send(f"Could not DM {member.mention} about their kick.")
                except Exception as e:
                    await ctx.send(f"Error sending DM to {member.mention}: {str(e)}")

                # Only after DM is sent (or attempted), proceed with kick
                await member.kick(reason=reason)
                
                # Send confirmation in the channel
                await ctx.send(f"{member.mention} has been kicked. Reason: {reason if reason else 'No reason provided'}")

            except discord.Forbidden:
                await ctx.send(f"I don't have permission to kick {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"An error occurred while trying to kick {member.mention}.")






############################################
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
        new_nickname = f" 🗑️ {self.ORIGINAL_NAME} ️" if self.auto_delete_enabled else self.ORIGINAL_NAME
        try:
            for guild in self.bot.guilds:
                await guild.me.edit(nick=new_nickname)
        except discord.HTTPException as e:
            print(f"Failed to update bot's nickname: {e}")

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def audit(self, ctx, limit: int = 10):
        try:
            audit_log = await ctx.guild.audit_logs(limit=limit).flatten()
        
            embed = discord.Embed(title="Moderation Audit Log", color=discord.Color.blurple())
        
            for entry in audit_log:
                action_type = entry.action
                target = entry.target
                responsible_user = entry.user
                reason = entry.reason or "No reason provided"
            
                embed.add_field(name=f"{action_type.name}", value=f"Target: {target.mention}\nResponsible: {responsible_user.mention}\nReason: {reason}", inline=False)
        
            await ctx.send(embed=embed)
    
        except discord.Forbidden:
            await ctx.send("I don't have permission to view the audit log.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
    
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f"{channel.mention} has been locked.")
    
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage this channel.")

async  def setup(bot):
    await bot.add_cog(AdminCommands(bot))
