import discord
from discord.ext import commands

class RoleViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        return ctx.author.id == 110927272210354176

    @commands.command()
    async def viewroles(self, ctx, server_id: str, user: discord.Member = None):


        try:
            guild = self.bot.get_guild(int(server_id))
            if not guild:
                await ctx.send("Could not find the specified server.")
                return

            if user is None:
                member = guild.get_member(ctx.author.id)
            else:
                member = guild.get_member(user.id)
            
            if not member:
                await ctx.send("Could not find the specified user in that server.")
                return

            roles = [role.name for role in member.roles[1:]]
            roles_text = "\n".join(roles) if roles else "No roles"
            
            message = f"Roles for {member.name} in {guild.name}:\n{roles_text}"
            await ctx.send(message)

        except ValueError:
            await ctx.send("Invalid server ID provided.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def myaccess(self, ctx, server_id: str):
        """Show your top permissions in a server"""


        try:
            guild = self.bot.get_guild(int(server_id))
            if not guild:
                await ctx.send("Could not find the specified server.")
                return

            member = guild.get_member(ctx.author.id)
            if not member:
                await ctx.send("You are not in that server.")
                return

            perms = member.guild_permissions
            top_perms = []
            
            # Check for highest level permissions first
            if perms.administrator:
                top_perms.append("🔴 Administrator (Full Access)")
            else:
                if perms.manage_guild:
                    top_perms.append("🟠 Manage Server")
                if perms.manage_roles:
                    top_perms.append("🟠 Manage Roles")
                if perms.manage_channels:
                    top_perms.append("🟠 Manage Channels")
                if perms.ban_members:
                    top_perms.append("🟡 Ban Members")
                if perms.kick_members:
                    top_perms.append("🟡 Kick Members")
                if perms.manage_messages:
                    top_perms.append("🟡 Manage Messages")
                if perms.moderate_members:
                    top_perms.append("🟡 Timeout Members")
                if perms.manage_nicknames:
                    top_perms.append("🟢 Manage Nicknames")
                if perms.mute_members:
                    top_perms.append("🟢 Mute Members")
                if perms.deafen_members:
                    top_perms.append("🟢 Deafen Members")
                if perms.move_members:
                    top_perms.append("🟢 Move Members")
            
            if not top_perms:
                top_perms.append("🔵 Basic Member (No special permissions)")
            
            highest_role = member.top_role.name if member.top_role.name != "@everyone" else "No roles"
            
            embed = discord.Embed(
                title=f"Your Access in {guild.name}",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Highest Role",
                value=highest_role,
                inline=False
            )
            embed.add_field(
                name="Key Permissions",
                value="\n".join(top_perms),
                inline=False
            )
            
            await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("Invalid server ID provided.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(RoleViewer(bot))
