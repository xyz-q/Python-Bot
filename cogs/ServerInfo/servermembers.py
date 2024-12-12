import discord
from discord.ext import commands

class ServerMembers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def servermembers(self, ctx, server_id: int = None):
        try:
            # If no server ID provided, use the current server
            if server_id is None:
                server = ctx.guild
            else:
                server = self.bot.get_guild(server_id)

            if server is None:
                await ctx.send("I couldn't find that server or I'm not in it.")
                return

            # Create initial embed for server information
            embed = discord.Embed(
                title=f"Server Information - {server.name}",
                color=discord.Color.blue()
            )
            
            # Add member count
            embed.add_field(
                name="Total Members", 
                value=str(server.member_count), 
                inline=False
            )

            # Categorize members
            owner = server.owner
            admins = []
            mods = []
            regular_members = []

            for member in server.members:
                member_name = f"{member.name}#{member.discriminator}"
                if member.nick:
                    member_name += f" ({member.nick})"

                # Check if member is owner
                if member == owner:
                    continue  # Skip owner as we'll add them separately
                # Check for admin permissions
                elif member.guild_permissions.administrator:
                    admins.append(member_name)
                # Check for moderator permissions (manage messages, ban members, kick members)
                elif any([member.guild_permissions.manage_messages,
                         member.guild_permissions.ban_members,
                         member.guild_permissions.kick_members]):
                    mods.append(member_name)
                else:
                    regular_members.append(member_name)

            # Send initial embed with hierarchy information
            await ctx.send(embed=embed)

            # Create and send Owner embed
            owner_embed = discord.Embed(
                title="Server Owner",
                description=f"{owner.name}#{owner.discriminator}" + (f" ({owner.nick})" if owner.nick else ""),
                color=discord.Color.gold()
            )
            await ctx.send(embed=owner_embed)

            # Create and send Admins embed
            if admins:
                admin_embed = discord.Embed(
                    title="Administrators",
                    description="\n".join(admins),
                    color=discord.Color.red()
                )
                await ctx.send(embed=admin_embed)

            # Create and send Mods embed
            if mods:
                mod_embed = discord.Embed(
                    title="Moderators",
                    description="\n".join(mods),
                    color=discord.Color.green()
                )
                await ctx.send(embed=mod_embed)

            # Split regular members into chunks and send
            if regular_members:
                chunks = [regular_members[i:i + 20] for i in range(0, len(regular_members), 20)]
                for i, chunk in enumerate(chunks):
                    member_embed = discord.Embed(
                        title=f"Regular Members (Part {i+1})",
                        description="\n".join(chunk),
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=member_embed)

        except discord.Forbidden:
            await ctx.send("I don't have permission to view that server's members.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(ServerMembers(bot))
