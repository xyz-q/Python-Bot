import discord
from discord.ext import commands
from datetime import datetime, timedelta

class MessageReader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.dm_only()
    @commands.command()
    async def messages(self, ctx, server_id: int, channel_id: int, limit: int = 50):
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send("Server not found! Please check the server ID.")
                return

            channel = guild.get_channel(channel_id)
            if not channel:
                await ctx.send("Channel not found! Please check the channel ID.")
                return

            messages_list = [f"Last {limit} messages from #{channel.name} in {guild.name}:\n"]
            
            async for message in channel.history(limit=limit, oldest_first=False):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content if message.content else "[No text content]"
                
                if message.attachments:
                    content += f" [+{len(message.attachments)} attachments]"
                
                msg_format = f"[{timestamp}] {message.author.name}: {content}"
                messages_list.append(msg_format)

            chunks = []
            current_chunk = ""
            
            for msg in messages_list:
                if len(current_chunk) + len(msg) + 2 > 1900:
                    chunks.append(current_chunk)
                    current_chunk = msg + "\n"
                else:
                    current_chunk += msg + "\n"
            
            if current_chunk:
                chunks.append(current_chunk)

            for chunk in chunks:
                await ctx.send(f"```\n{chunk}```")

        except discord.Forbidden:
            await ctx.send("I don't have permission to read messages in that channel!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @messages.error
    async def messages_error(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in DMs!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide both server ID and channel ID!\n"
                         "Usage: ,messages <server_id> <channel_id> [limit]")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide valid server and channel IDs (numbers only)!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(MessageReader(bot))
