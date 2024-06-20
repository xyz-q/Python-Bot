import discord
from discord.ext import commands

previous_roles = {}

class RoleCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="jail", description="Banish a member to jail.")
    async def jail(self, ctx, member: discord.Member):
        global previous_roles
        jail_role = discord.utils.get(ctx.guild.roles, name=".jail")
        if not jail_role:
            await ctx.send("The .jail role does not exist.")
            return

        previous_roles[member.id] = [role.id for role in member.roles]
        await member.edit(roles=[jail_role])
        if jail_role in member.roles:
            await ctx.send(f"{member.display_name} has been banished.")
        else:
            await ctx.send(f"Failed to banish {member.display_name}.")

    @commands.command(name="release", description="Release a member from jail.")
    async def release(self, ctx, member: discord.Member):
        global previous_roles
        jail_role = discord.utils.get(ctx.guild.roles, name=".jail")
        if not jail_role:
            await ctx.send("The .jail role does not exist.")
            return

        await member.remove_roles(jail_role)
        roles_to_add = [ctx.guild.get_role(role_id) for role_id in previous_roles.get(member.id, [])]
        if roles_to_add:
            await member.edit(roles=roles_to_add)
            await ctx.send(f"{member.display_name} has been released from jail. Their previous roles have been restored.")
        else:
            await ctx.send("Failed to restore previous roles.")

    @commands.command(name="role", description="Add or remove a role from a member.")
    async def role(self, ctx, *, args: str):
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("I don't have permission to manage roles.")
            return

        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You don't have permission to manage roles.")
            return

        args = args.split()
        if len(args) != 2:
            await ctx.send("Please provide both a member and a role.")
            return

        member_str, role_str = args
        member = discord.utils.get(ctx.guild.members, mention=member_str)
        if role_str.startswith("<@&") and role_str.endswith(">"):
            role_id = role_str[3:-1]
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_str)

        if member is None or role is None:
            await ctx.send("Invalid member or role provided.")
            return

        if ctx.guild.me.top_role <= role:
            await ctx.send("I can't manage roles higher than my top role.")
            return

        if ctx.author.top_role <= role:
            await ctx.send("You can't manage roles higher than your top role.")
            return

        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"Removed the {role.name} role from {member.mention}.")
        else:
            await member.add_roles(role)
            await ctx.send(f"Added the {role.name} role to {member.mention}.")

async def setup(bot):
    await bot.add_cog(RoleCmds(bot))
