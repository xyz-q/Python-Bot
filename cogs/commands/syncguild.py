import discord
from discord.ext import commands

class SyncGuild(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="syncguild", description="Sync slash commands to a specific guild.")
    @commands.has_permissions(administrator=True)
    async def sync_guild(self, ctx, guild_id_or_name: str, test: bool = False):
        try:
            # Try to get the guild by ID
            guild = self.bot.get_guild(int(guild_id_or_name))
            if not guild:
                # If not found by ID, try to get the guild by name
                guild = discord.utils.get(self.bot.guilds, name=guild_id_or_name)
            if not guild:
                await ctx.send(f"Could not find a guild with the ID or name '{guild_id_or_name}'.")
                return

            if test:
                await ctx.send("Testing slash commands...")
                await self.bot.tree.sync(guild=guild)
                await ctx.send("Slash commands tested successfully!")
            else:
                await ctx.send(f"Initiating slash command synchronization for guild: {guild.name} ({guild.id}). This may take a few minutes to complete.")
                await self.bot.tree.sync(guild=guild)
                await ctx.send(f"Slash commands synchronized successfully for guild: {guild.name} ({guild.id}).")
        except ValueError:
            await ctx.send(f"Invalid guild ID or name: '{guild_id_or_name}'.")
        except Exception as e:
            await ctx.send(f"Failed to sync/test slash commands: {e}")

    @commands.command(name="clearcache", description="Clear the slash command cache.")
    @commands.has_permissions(administrator=True)
    async def clear_cache(self, ctx):
        try:
        # Get all the registered slash commands
            registered_commands = await self.bot.tree.fetch_commands()

        # Delete all the registered slash commands
            for command in registered_commands:
                await command.delete()

            await ctx.send("Slash command cache cleared successfully.")
        except Exception as e:
            await ctx.send(f"Failed to clear slash command cache: {e}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SyncGuild(bot))