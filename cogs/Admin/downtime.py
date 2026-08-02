import discord
from discord.ext import commands
from datetime import datetime, timezone


class DowntimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="downtime")
    @commands.is_owner()
    async def downtime(self, ctx, *, message=None):
        """
        Notify all server owners about planned downtime.

        Usage:
        ,downtime <message>
        """

        if not message:
            message = (
                "The bot will be temporarily offline for maintenance.\n"
                "Please check the bot status channel for updates."
            )

        sent = []
        failed = []

        embed = discord.Embed(
            title="Bot Downtime Notice",
            description=message,
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_footer(
            text=f"Sent by {ctx.author}"
        )

        for guild in self.bot.guilds:
            try:
                owner = guild.owner

                if owner is None:
                    owner = await guild.fetch_owner()

                await owner.send(embed=embed)
                sent.append(guild.name)

            except discord.Forbidden:
                failed.append(f"{guild.name} (DMs disabled)")

            except Exception as e:
                failed.append(f"{guild.name} ({e})")

        result = discord.Embed(
            title="Downtime Notification Complete",
            color=discord.Color.green()
        )

        result.add_field(
            name="Sent",
            value="\n".join(sent) if sent else "None",
            inline=False
        )

        result.add_field(
            name="Failed",
            value="\n".join(failed) if failed else "None",
            inline=False
        )

        await ctx.send(embed=result)


async def setup(bot):
    await bot.add_cog(DowntimeCog(bot))