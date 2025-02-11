import discord
from discord.ext import commands
import os

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "/data/maintenance_config.txt"
        self.maintenance_mode = self.load_maintenance_state()

    def load_maintenance_state(self):
        """Load maintenance state from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    state = f.read().strip()
                    return state.lower() == 'true'
        except Exception as e:
            print(f"Error loading maintenance state: {e}")
        return False

    def save_maintenance_state(self):
        """Save maintenance state to file"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                f.write(str(self.maintenance_mode))
        except Exception as e:
            print(f"Error saving maintenance state: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def maintenance(self, ctx):
        """Toggle maintenance mode for the bot"""
        self.maintenance_mode = not self.maintenance_mode
        self.save_maintenance_state()  # Save the new state
        await self.update_bot_nickname()
        
        status = "enabled" if self.maintenance_mode else "disabled"
        await ctx.send(f"Maintenance mode {status}")

    async def update_bot_nickname(self):
        """Update the bot's nickname in all guilds"""
        for guild in self.bot.guilds:
            try:
                # Get current nickname or default to bot's name
                current_nickname = guild.me.nick or guild.me.name

                # Remove [MAINTENANCE] prefix if it exists
                if current_nickname.startswith("[MAINTENANCE] "):
                    original_name = current_nickname[13:]
                else:
                    original_name = current_nickname

                # Build new nickname based on maintenance mode
                if self.maintenance_mode:
                    new_nickname = f"[MAINTENANCE] {original_name}"
                else:
                    new_nickname = original_name

                # Ensure nickname doesn't exceed Discord's 32 character limit
                if len(new_nickname) > 32:
                    new_nickname = new_nickname[:32]

                # Only update if the nickname is different
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

async def setup(bot):
    await bot.add_cog(Maintenance(bot))
