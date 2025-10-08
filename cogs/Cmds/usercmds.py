import discord
from discord.ext import commands
import json
import os

AFK_FILE = ".json/afk_data.json"

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = self.load_afk_data()

    def load_afk_data(self):
        if os.path.exists(AFK_FILE):
            with open(AFK_FILE, 'r') as file:
                return json.load(file)
        else:
            return {}

    def save_afk_data(self):
        with open(AFK_FILE, 'w') as file:
            json.dump(self.afk_users, file, indent=4)

    @commands.command()
    async def names(self, ctx, member: discord.Member):
        async for entry in ctx.guild.audit_logs(limit=None, action=discord.AuditLogAction.member_update):

            if entry.target == member:
                old_nick = entry.before.nick
                if old_nick:
                    await ctx.send(f"Old nickname for {member.display_name}: {old_nick}")
                else:
                    await ctx.send(f"{member.display_name} has not changed their nickname.")
                return
        await ctx.send(f"No nickname change found for {member.display_name}.")

    @commands.command()
    async def user(self, ctx, member: discord.Member = None, user_id: int = None):
        if user_id:
            try:
                member = await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                await ctx.send("User not found.")
                return
        else:
            member = member or ctx.author

        embed = discord.Embed(title=f"User Info - {member.display_name}", color=member.color)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            default_avatar_url = member.default_avatar.url
            embed.set_thumbnail(url=default_avatar_url)

        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Nickname", value=member.display_name, inline=False)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%a, %d %B %Y, %I:%M %p UTC"), inline=False)
        embed.add_field(name="Join Date", value=member.joined_at.strftime("%a, %d %B %Y, %I:%M %p UTC"), inline=False)

        if member.activity is not None:
            embed.add_field(name="Activity", value=member.activity.name, inline=False)

        boosting_role = discord.utils.get(member.roles, name="Server Booster")
        boosting_status = "Yes" if boosting_role else "No"
        embed.add_field(name="Boosting this Server", value=boosting_status, inline=True)

        top_role = member.top_role.name
        embed.add_field(name="Top Role", value=top_role, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='avatar', aliases=['pfp', 'pic'])
    async def avatar(self, ctx, user: discord.User = None, user_id: int = None):
        if user_id:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                await ctx.send("User not found.")
                return
        else:
            user = user or ctx.author

        if user.avatar:
            avatar_url = user.avatar.url
        else:
            avatar_url = user.default_avatar.url

        embed = discord.Embed(title=f"{user.name}'s Avatar", color=ctx.author.color)
        embed.set_image(url=avatar_url)

        await ctx.send(embed=embed)

    @commands.command()
    async def afk(self, ctx, *, reason=""):
        user_id = str(ctx.author.id)
        afk_role = discord.utils.get(ctx.guild.roles, name='.afk')

        if user_id in self.afk_users:
            self.afk_users.pop(user_id)
            self.save_afk_data()
            
            # Remove role
            if afk_role and afk_role in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(afk_role)
                except discord.Forbidden:
                    pass
            
            # Remove {afk} from current nickname
            try:
                current_nick = ctx.author.nick
                if current_nick and current_nick.startswith("{afk}"):
                    # Extract the name after the {afk} tag
                    original_name = current_nick[5:].strip()
                    await ctx.author.edit(nick=original_name if original_name else None)
            except discord.Forbidden:
                pass
                
            await ctx.send(f"{ctx.author.mention} is no longer AFK.")
        else:
            self.afk_users[user_id] = reason
            self.save_afk_data()
            
            # Add role
            if afk_role:
                try:
                    await ctx.author.add_roles(afk_role)
                except discord.Forbidden:
                    pass
            
            # Add {afk} to current nickname
            try:
                current_nickname = ctx.author.nick
                if current_nickname and current_nickname.startswith("{afk}"):
                    # Already has {afk}, don't add again
                    pass
                else:
                    # Use current nickname or default username as the original name
                    original_name = ctx.author.nick or ctx.author.name
                    new_nickname = f"{{afk}} {original_name}"
                    
                    # Ensure the nickname doesn't exceed 32 characters
                    if len(new_nickname) > 32:
                        new_nickname = new_nickname[:32]
                    
                    await ctx.author.edit(nick=new_nickname)
            except discord.Forbidden:
                pass
                
            display_reason = reason if reason else "N/A"
            await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {display_reason}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Detect nickname changes and re-add {afk} if user is AFK"""
        user_id = str(after.id)
        
        # Only care about nickname changes for AFK users
        if user_id in self.afk_users and before.nick != after.nick:
            # Check if the new nickname doesn't have {afk} at the start
            if after.nick and not after.nick.startswith("{afk}"):
                try:
                    new_nickname = f"{{afk}} {after.nick}"
                    
                    # Ensure the nickname doesn't exceed 32 characters
                    if len(new_nickname) > 32:
                        new_nickname = new_nickname[:32]
                    
                    await after.edit(nick=new_nickname)
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        mentioned_afk_users = [user_id for user_id in self.afk_users if message.guild.get_member(int(user_id)) in message.mentions]
        if mentioned_afk_users:
            for user_id in mentioned_afk_users:
                reason = self.afk_users[user_id]
                user = message.guild.get_member(int(user_id))
                display_reason = reason if reason else "N/A"
                await message.channel.send(f"{user.mention} is currently AFK. Reason: {display_reason}")


    @commands.command(name='nickname', aliases=['nick'])
    @commands.is_owner()
    async def change_nickname(self, ctx, member: discord.Member, *, new_nickname=None):
        try:
            old_nickname = member.display_name
            
            await member.edit(nick=new_nickname)
            
            if new_nickname:
                await ctx.send(f"Changed {old_nickname}'s nickname to {new_nickname}")
            else:
                await ctx.send(f"Reset {old_nickname}'s nickname")
                
        except discord.Forbidden:
            await ctx.send("I don't have permission to change that user's nickname!")
        except discord.HTTPException:
            await ctx.send("Failed to change nickname. Make sure the nickname is not too long.")



async def setup(bot):
    await bot.add_cog(UserCommands(bot))
