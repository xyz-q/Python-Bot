import discord
from discord.ext import commands

class ServerInvite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        return ctx.author.id == 110927272210354176


    @commands.command()
    async def inviteserver(self, ctx, server_id: int):
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send("Server not found! Please check the server ID.")
                return

            invite_channel = None
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    permissions = channel.permissions_for(guild.me)
                    if permissions.create_instant_invite:
                        invite_channel = channel
                        break

            if not invite_channel:
                await ctx.send("I don't have permission to create invites in any channel in this server!")
                return

            invite = await invite_channel.create_invite(
                max_age=86400,
                max_uses=1,
                unique=True,
                reason=f"Invite requested by {ctx.author.name} via DM"
            )

            await ctx.send(f"Here's your invite link for {guild.name}:\n{invite.url}\n"
                         f"This invite will expire in 24 hours and can only be used once.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to create invites in this server!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def checkinvites(self, ctx):
        """Check who invited the bot to each server"""
        for guild in self.bot.guilds:
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=10):
                    if entry.target.id == self.bot.user.id:
                        await ctx.send(f"**{guild.name}** - Invited by {entry.user.name}#{entry.user.discriminator} on {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        break
                else:
                    await ctx.send(f"**{guild.name}** - No audit log found (missing permissions or too old)")
            except discord.Forbidden:
                await ctx.send(f"**{guild.name}** - No audit log access")
            except Exception as e:
                await ctx.send(f"**{guild.name}** - Error: {str(e)}")


    @inviteserver.error
    async def inviteserver_error(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in DMs!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the server ID!\n"
                         "Usage: ,inviteserver <server_id>")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid server ID (numbers only)!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(ServerInvite(bot))
