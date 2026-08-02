import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional


class KickSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="The reason for the kick"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        bot_member = guild.me

        if not bot_member.guild_permissions.kick_members:
            await interaction.response.send_message(
                "I don't have permission to kick members!",
                ephemeral=True
            )
            return

        if interaction.user.top_role <= member.top_role:
            await interaction.response.send_message(
                "You cannot kick this member as their role is higher than or equal to yours!",
                ephemeral=True
            )
            return

        if bot_member.top_role <= member.top_role:
            await interaction.response.send_message(
                "I cannot kick this member as their role is higher than mine!",
                ephemeral=True
            )
            return

        try:
            try:
                await member.send(
                    f"You have been kicked from {guild.name}\nReason: {reason}"
                )
            except discord.HTTPException:
                pass

            await member.kick(reason=reason)

            embed = discord.Embed(
                title="Member Kicked",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="Kicked User",
                value=member.mention,
                inline=False
            )
            embed.add_field(
                name="Kicked By",
                value=interaction.user.mention,
                inline=False
            )
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to kick this member!",
                ephemeral=True
            )

        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"An error occurred while kicking the member: {e}",
                ephemeral=True
            )

    @kick.error
    async def kick_error(
        self,
        interaction: discord.Interaction,
        error
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to kick members!",
                ephemeral=True
            )
        else:
            print(f"Kick command error: {error}")


async def setup(bot):
    await bot.add_cog(KickSystem(bot))