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

    @commands.command()
    @commands.is_owner()
    async def maintenance(self, ctx):
        """Toggle maintenance mode for the bot"""
        self.maintenance_mode = not self.maintenance_mode
        self.save_maintenance_state()  # Save the new state
        await self.update_bot_nickname()
        
        status = "enabled" if self.maintenance_mode else "disabled"
        await ctx.send(f"Maintenance mode {status}")

    @commands.command()
    @commands.is_owner()
    async def resetname(self, ctx):
        """Reset bot nickname to default in all servers"""
        for guild in self.bot.guilds:
            try:
                await guild.me.edit(nick=xyz)
            except (discord.HTTPException, discord.Forbidden) as e:
                print(f"Failed to reset nickname in {guild.name}: {e}")
        await ctx.send("Bot nickname reset in all servers")

    async def update_bot_nickname(self):
        """Update the bot's nickname in all guilds"""
        for guild in self.bot.guilds:
            try:
                # Get current nickname
                current_nickname = guild.me.nick
                
                # Extract original name by removing all maintenance prefixes
                if current_nickname:
                    original_name = current_nickname
                    while original_name.startswith("[MAINTENANCE] "):
                        original_name = original_name[13:]
                else:
                    original_name = guild.me.name

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
