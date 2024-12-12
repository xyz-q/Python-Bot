import discord
from discord.ext import commands

class RoleViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def viewroles(self, ctx, server_id: str, user: discord.Member = None):  # Added 'self' parameter
        # Check if the command is being used in DMs
        if ctx.guild is not None:
            await ctx.send("This command can only be used in DMs!")
            return

        try:
            # Get the server using the provided ID
            guild = self.bot.get_guild(int(server_id))  # Changed bot to self.bot
            if not guild:
                await ctx.send("Could not find the specified server.")
                return

            # If no user is specified, use the command invoker
            if user is None:
                member = guild.get_member(ctx.author.id)
            else:
                member = guild.get_member(user.id)
            
            if not member:
                await ctx.send("Could not find the specified user in that server.")
                return

            # Create a formatted list of roles
            roles = [role.name for role in member.roles[1:]]  # [1:] to exclude @everyone
            roles_text = "\n".join(roles) if roles else "No roles"
            
            message = f"Roles for {member.name} in {guild.name}:\n{roles_text}"
            await ctx.send(message)

        except ValueError:
            await ctx.send("Invalid server ID provided.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(RoleViewer(bot))
