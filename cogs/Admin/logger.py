import discord
from discord.ext import commands
import traceback
import sys
from datetime import datetime

class ErrorLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the original error
        if hasattr(error, 'original'):
            error = error.original
        
        # Create single, clean error message
        error_message = f"ERROR-ERRORTEST: [{timestamp}]"
        
        # Print only once and stop propagation
        print(error_message, file=sys.stderr)
        
        # Prevent further error handling
        error.handled = True
        return

    # Disable default error handling
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        pass



    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the error message with a generic cog name since we can't determine it
        error_message = f"ERROR-GLOBAL: [{timestamp}] An error occurred in {event}"
        
        # Print to terminal
        print(error_message, file=sys.stderr)
        
        # Get the error information
        _, error, error_traceback = sys.exc_info()
        
        # Print the full traceback
        print(''.join(traceback.format_exception(type(error), error, error_traceback)))

async def setup(bot):
    await bot.add_cog(ErrorLogger(bot))
