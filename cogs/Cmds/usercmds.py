import discord
from discord.ext import commands
import json
import os

AFK_FILE = "afk_data.json"

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

        if user_id in self.afk_users:
            self.afk_users.pop(user_id)
            self.save_afk_data()
            await ctx.send(f"{ctx.author.mention} is no longer AFK.")
        else:
            self.afk_users[user_id] = reason
            self.save_afk_data()
            await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        mentioned_afk_users = [user_id for user_id in self.afk_users if message.guild.get_member(int(user_id)) in message.mentions]
        if mentioned_afk_users:
            for user_id in mentioned_afk_users:
                reason = self.afk_users[user_id]
                user = message.guild.get_member(int(user_id))
                await message.channel.send(f"{user.mention} is currently AFK. Reason: {reason}")


    @commands.command(name='nickname', aliases=['nick'])
    @commands.is_owner()
    async def change_nickname(self, ctx, member: discord.Member, *, new_nickname=None):
        try:
            # Store old nickname for confirmation message
            old_nickname = member.display_name
            
            # Change the nickname
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
