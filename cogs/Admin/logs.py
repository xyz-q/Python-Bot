import discord
from discord.ext import commands
from datetime import datetime
import os

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Create logs directory if it doesn't exist
        if not os.path.exists('textlogs'):
            os.makedirs('textlogs')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots (including self)
        if message.author.bot:
            return

        # Format the log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message.guild.name} #{message.channel.name} - {message.author.name}: {message.content}\n"

        # Log to console
        print(log_entry.strip())

        # Log to file (named by date)
        filename = f"textlogs/chat_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(log_entry)

async def setup(bot):
    await bot.add_cog(MessageLogger(bot))
