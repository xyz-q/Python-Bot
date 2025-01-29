import discord
from discord.ext import commands

previous_roles = {}

class RoleCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

 


    @commands.command(name="role", description="Add or remove a role from a member.")
    async def role(self, ctx, *, args: str):
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("I don't have permission to manage roles.")
            return



        args = args.split()
        if len(args) != 2:
            await ctx.send("Please provide both a member and a role.")
            return

        member_str, role_str = args
        
        # Check if role_str is a role ID
        if role_str.isdigit():
            role = discord.utils.get(ctx.guild.roles, id=int(role_str))
        elif role_str.startswith("<@&") and role_str.endswith(">"):
            role_id = role_str[3:-1]
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_str)

        if role is None:
            await ctx.send("Invalid role provided, make sure the proper syntax is used. (,role <@user> <@role>)")
            return

        if ctx.guild.me.top_role <= role:
            await ctx.send("I can't manage roles higher than my top role.")
            return

        if ctx.author.top_role <= role:
            await ctx.send("You can't manage roles higher than your top role.")
            return

        if member_str.lower() == "everyone":
            members = ctx.guild.members
        else:
            member = discord.utils.get(ctx.guild.members, mention=member_str)
            if member is None:
                await ctx.send("Invalid member provided, make sure the proper syntax is used. (,role <@user> <@role>)")
                return
            members = [member]

        for member in members:
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed the {role.name} role from {member.mention}.")
            else:
                await member.add_roles(role)
                await ctx.send(f"Added the {role.name} role to {member.mention}.")

    @commands.is_owner()
    @commands.command()
    async def addrole(self, ctx, *, role_name: str):
        guild = ctx.guild
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("I don't have permission to manage roles.")
            return        
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            await ctx.send(f"The role `{role_name}` already exists.")
        else:
            await guild.create_role(name=role_name)
            await ctx.send(f"Created the role `{role_name}`.")

    @commands.is_owner()
    @commands.command()
    async def removerole(self, ctx, *, role_name: str):
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await role.delete()
            await ctx.send(f"Deleted the role `{role_name}`.")
        else:
            await ctx.send(f"The role `{role_name}` does not exist.")


    @commands.command(name="roles", description="List all roles and their IDs.")
    async def roles(self, ctx):
        # Get all roles and sort them by position in descending order (highest to lowest)
        roles = sorted(ctx.guild.roles, key=lambda x: x.position, reverse=True)
        
        # Filter out @everyone role and create the role list
        role_list = "\n".join([f"{role.name}: {role.id}" for role in roles if role.name != "@everyone"])
        
        await ctx.send(f"Roles in this server:\n{role_list}")


async def setup(bot):
    await bot.add_cog(RoleCmds(bot))
