import discord
from discord.ext import commands

# Define a global dictionary to store previous roles of users
previous_roles = {}

class RoleCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="jail", description="Banish a member to jail.")
    async def jail(self, ctx, member: discord.Member):
        global previous_roles

        # Check if the role exists
        jail_role = discord.utils.get(ctx.guild.roles, name=".jail")

        if not jail_role:
            await ctx.send("The .jail role does not exist.")
            return

        # Store the user's current roles
        previous_roles[member.id] = [role.id for role in member.roles]

        # Remove all other roles
        await member.edit(roles=[jail_role])

        # Toggle the .jail role
        if jail_role in member.roles:
            await ctx.send(f"{member.display_name} has been banished.")
        else:
            await ctx.send(f"Failed to banish {member.display_name}.")

    @commands.command(name="release", description="Release a member from jail.")
    async def release(self, ctx, member: discord.Member):
        global previous_roles

        # Check if the role exists
        jail_role = discord.utils.get(ctx.guild.roles, name=".jail")

        if not jail_role:
            await ctx.send("The .jail role does not exist.")
            return

        # Remove the .jail role
        await member.remove_roles(jail_role)

        # Restore the user's previous roles
        roles_to_add = [ctx.guild.get_role(role_id) for role_id in previous_roles.get(member.id, [])]
        if roles_to_add:
            await member.edit(roles=roles_to_add)
            await ctx.send(f"{member.display_name} has been released from jail. Their previous roles have been restored.")
        else:
            await ctx.send("Failed to restore previous roles.")

    @commands.command(name="role", description="Add or remove a role from a member.")
    async def role(self, ctx, *, args: str):
        # Check if the bot has permission to manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("I don't have permission to manage roles.")
            return

        # Check if the caller has permission to manage roles
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You don't have permission to manage roles.")
            return

        # Parse the arguments
        args = args.split()
        if len(args) != 2:
            await ctx.send("Please provide both a member and a role.")
            return

        member_str, role_str = args
        member = discord.utils.get(ctx.guild.members, mention=member_str)

        # Extract role from mention
        if role_str.startswith("<@&") and role_str.endswith(">"):
            role_id = role_str[3:-1]
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_str)

        # Check if a member and role are provided
        if member is None or role is None:
            await ctx.send("Invalid member or role provided.")
            return

        # Check if the bot can manage the role
        if ctx.guild.me.top_role <= role:
            await ctx.send("I can't manage roles higher than my top role.")
            return

        # Check if the user can manage the role
        if ctx.author.top_role <= role:
            await ctx.send("You can't manage roles higher than your top role.")
            return

        # Check if the member already has the role
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"Removed the {role.name} role from {member.mention}.")
        else:
            await member.add_roles(role)
            await ctx.send(f"Added the {role.name} role to {member.mention}.")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(RoleCmds(bot))
