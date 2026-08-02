import discord
from discord.ext import commands
import json
from datetime import datetime, timezone

class MaintenanceMode(commands.CheckFailure):
    pass
class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = ".json/maintenance.json"
        self.maintenance_mode = self.load_maintenance_state()

    def create_blocked_embed(self):
        return discord.Embed(
            title="🔧 Maintenance Mode",
            description="Commands are temporarily disabled while the bot is being updated.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

    def create_embed(self, enabled: bool):
        if enabled:
            embed = discord.Embed(
                title="🔧 Bot Maintenance",
                description=(
                    "The bot is currently undergoing maintenance.\n\n"
                    "Commands have temporarily been disabled for users.\n"
                    "The bot will return once maintenance is complete."
                ),
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )



            embed.add_field(
                name="Status",
                value="<a:orangealert:1336885812062584862> Maintenance Active",
                inline=True
            )

            embed.add_field(
                name="Access",
                value="Owner testing enabled",
                inline=True
            )

        else:
            embed = discord.Embed(
                title="<a:greenalert:1336886706216894524> Bot Online",
                description=(
                    "Maintenance has been completed.\n\n"
                    "All commands are now available again."
                ),
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="Status",
                value="<a:greenalert:1336886706216894524> Online",
                inline=True
            )

        embed.set_footer(text="ZXPQ Bot Maintenance")

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        return embed

    def load_maintenance_state(self):
        """Load maintenance state from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error loading maintenance state: {e}")
            return False

    def save_maintenance_state(self):
        """Save maintenance state to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.maintenance_mode, f)
        except Exception as e:
            print(f"Error saving maintenance state: {e}")

    async def notify_guild_owners(self, enabled: bool):
        embed = self.create_embed(enabled)

        for guild in self.bot.guilds:
            owner = guild.owner

            if owner is None:
                continue

            try:
                await owner.send(embed=embed)

            except discord.Forbidden:
                pass

            except Exception as e:
                print(f"Failed to notify owner of {guild.name}: {e}")

    @commands.command()
    @commands.is_owner()
    async def maintenance(self, ctx):
        """Toggle maintenance mode for the bot"""
        self.maintenance_mode = not self.maintenance_mode
        self.save_maintenance_state()
        await self.update_bot_nickname()

        # Notify guild owners
        await self.notify_guild_owners(self.maintenance_mode)

        await ctx.send(
            embed=self.create_embed(self.maintenance_mode)
        )

    @commands.command()
    @commands.is_owner()
    async def resetname(self, ctx):
        """Reset bot nickname to default in all servers"""
        for guild in self.bot.guilds:
            try:
                await guild.me.edit(nick=None)
            except (discord.HTTPException, discord.Forbidden) as e:
                print(f"Failed to reset nickname in {guild.name}: {e}")
        await ctx.send("Bot nickname reset in all servers")

    async def update_bot_nickname(self):
        """Update the bot's nickname in all guilds"""
        for guild in self.bot.guilds:
            try:
                current_nickname = guild.me.nick

                # Extract original name
                if current_nickname:
                    original_name = current_nickname
                    while original_name.startswith("[MAINTENANCE] "):
                        original_name = original_name[13:]
                else:
                    original_name = guild.me.name

                # Build nickname
                if self.maintenance_mode:
                    new_nickname = f"[MAINTENANCE] {original_name}"
                else:
                    new_nickname = original_name

                # Discord nickname limit
                new_nickname = new_nickname[:32]

                if guild.me.nick != new_nickname:
                    await guild.me.edit(nick=new_nickname)

            except discord.HTTPException as e:
                print(f"Failed to update bot's nickname in {guild.name}: {e}")
            except discord.Forbidden as e:
                print(f"Missing permissions to update nickname in {guild.name}: {e}")
                
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, MaintenanceMode):
            await ctx.send(
                embed=self.create_blocked_embed(),
                delete_after=5
            )
            return



    @commands.Cog.listener()
    async def on_ready(self):
        """Update nicknames when bot starts up"""
        await self.update_bot_nickname()


# ---------------------------
# GLOBAL MAINTENANCE CHECK
# ---------------------------

async def maintenance_check(ctx):
    """Global maintenance lock"""
    cog = ctx.bot.get_cog("Maintenance")

    # Allow if Maintenance cog isn't loaded
    if not cog:
        return True

    # Owner bypass
    if await ctx.bot.is_owner(ctx.author):
        return True

    # Block everyone else
    if cog.maintenance_mode:
        raise MaintenanceMode()

    return True

async def setup(bot):
    await bot.add_cog(Maintenance(bot))
    bot.add_check(maintenance_check)
