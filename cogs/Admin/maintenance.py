import discord
from discord.ext import commands
import json

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = ".json/maintenance.json"
        self.maintenance_mode = self.load_maintenance_state()

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
        """DM all guild owners when maintenance starts or ends"""
        title = "Bot Maintenance Started" if enabled else "Bot Maintenance Complete"
        desc = (
            "The bot is currently undergoing maintenance.\n"
            "Commands are temporarily disabled for users.\n"
            "The bot will return once maintenance is complete."
            if enabled else
            "The bot is back online and commands are available again."
        )

        for guild in self.bot.guilds:
            owner = guild.owner
            if owner is None:
                continue

            try:
                await owner.send(f"**{title}**\n\n{desc}")
            except discord.Forbidden:
                # Owner has DMs disabled — ignore silently
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

        status = "enabled" if self.maintenance_mode else "disabled"
        await ctx.send(f"Maintenance mode {status}")

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
    async def on_ready(self):
        """Update nicknames when bot starts up"""
        await self.update_bot_nickname()


# ---------------------------
# GLOBAL MAINTENANCE CHECK
# ---------------------------

async def maintenance_check(ctx):
    """Global check that blocks commands during maintenance"""
    cog = ctx.bot.get_cog("Maintenance")

    # If cog not loaded, allow commands
    if not cog:
        return True

    # Owner bypass
    if await ctx.bot.is_owner(ctx.author):
        return True

    # If maintenance mode is active, block all commands
    if cog.maintenance_mode:
        await ctx.send(
            "The bot is currently in maintenance mode. Commands are disabled.",
            delete_after=7
        )
        return False

    return True


async def setup(bot):
    bot.add_check(maintenance_check)
    await bot.add_cog(Maintenance(bot))
