from discord.ext import commands
import discord
import os

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='devlist', aliases=['devcmds', 'devcommands'], help='Displays a list of all bot commands')
    async def commands_list(self, ctx):
        await ctx.message.delete()
        
        # Group commands by cog
        cog_commands = {}
        for command in self.bot.commands:
            cog_name = command.cog.qualified_name if command.cog else "No Cog"
            if cog_name not in cog_commands:
                cog_commands[cog_name] = []
            cog_commands[cog_name].append(command.name)
        
        # Sort cogs and commands
        formatted_commands = []
        for cog_name in sorted(cog_commands.keys()):
            # Get file name from cog
            cog_obj = self.bot.get_cog(cog_name)
            if cog_obj:
                file_name = os.path.basename(cog_obj.__module__.split('.')[-1])
                formatted_commands.append(f"\n**{file_name}.py > {cog_name}**")
            else:
                formatted_commands.append(f"\n**{cog_name}**")
            
            # Sort and add commands
            for cmd in sorted(cog_commands[cog_name]):
                formatted_commands.append(f"• {cmd}")

        message_content = "**Commands by File > Cog > Command**\n" + "\n".join(formatted_commands)
        
        message = await ctx.send(message_content)
        await message.delete(delay=60)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))
