from discord.ext import commands
import discord

# Import your hardcoded list from list.py
from cogs.Cmds.list import commands_list

class CommandComparison(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='compare')
    async def compare_commands(self, ctx):
        """Compare devlist (actual commands) with list (hardcoded) to find missing commands"""
        await ctx.message.delete()
        
        # Get actual bot commands (same as devlist)
        actual_commands = set(command.name for command in self.bot.commands)
        
        # Extract command names from hardcoded list (remove commas and slashes)
        hardcoded_commands = set()
        for cmd_info in commands_list:
            if not cmd_info or len(cmd_info) == 0:
                continue
            cmd_name = cmd_info[0].strip()
            if not cmd_name:
                continue
            # Remove prefix and extract base command name
            if cmd_name.startswith(','):
                cmd_name = cmd_name[1:].split()[0] if len(cmd_name) > 1 else ""
            elif cmd_name.startswith('/'):
                cmd_name = cmd_name[1:].split()[0] if len(cmd_name) > 1 else ""
            if cmd_name:
                hardcoded_commands.add(cmd_name)
        
        # Find missing commands
        missing_in_list = actual_commands - hardcoded_commands
        missing_in_bot = hardcoded_commands - actual_commands
        
        embed = discord.Embed(title="Command Comparison", color=discord.Color.blue())
        
        if missing_in_list:
            missing_text = "\n".join(f"`,{cmd}`" for cmd in sorted(missing_in_list))
            if len(missing_text) > 1020:
                missing_text = missing_text[:1020] + "..."
            embed.add_field(
                name="❌ Missing from ,list (in bot but not in hardcoded list)",
                value=missing_text or "None",
                inline=False
            )
        
        if missing_in_bot:
            bot_text = "\n".join(f"`,{cmd}`" for cmd in sorted(missing_in_bot))
            if len(bot_text) > 1020:
                bot_text = bot_text[:1020] + "..."
            embed.add_field(
                name="⚠️ In ,list but not in bot (hardcoded but no actual command)",
                value=bot_text or "None",
                inline=False
            )
        
        embed.add_field(
            name="📊 Summary",
            value=f"Total bot commands: {len(actual_commands)}\n"
                  f"Total hardcoded: {len(hardcoded_commands)}\n"
                  f"Missing from list: {len(missing_in_list)}\n"
                  f"Outdated in list: {len(missing_in_bot)}",
            inline=False
        )
        
        await ctx.send(embed=embed, delete_after=120)

async def setup(bot):
    await bot.add_cog(CommandComparison(bot))