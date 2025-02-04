import discord
from discord.ext import commands

class RoleViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def viewroles(self, ctx, server_id: str, user: discord.Member = None):
        if ctx.guild is not None:
            await ctx.send("This command can only be used in DMs!")
            return

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

async def setup(bot):
    await bot.add_cog(RoleViewer(bot))
