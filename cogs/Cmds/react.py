import discord
from discord.ext import commands

class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="react")
    async def react(self, ctx, partial_channel_name: str, message_id: int, emoji: str):
        """
        React to a message in a channel whose name matches (even partially) the input.
        Handles channels with emojis in their names.
        Usage: ,react <partial_channel_name> <message_id> <emoji>
        """
        try:
            channel = discord.utils.find(
                lambda c: partial_channel_name.lower() in c.name.lower(),
                ctx.guild.text_channels,
            )

            if not channel:
                await ctx.send(f"No channel found matching '{partial_channel_name}'.")
                return

            message = await channel.fetch_message(message_id)

            await message.add_reaction(emoji)
            await ctx.send(f"Reacted to message ID {message_id} in channel #{channel.name} with {emoji}!")

        except discord.NotFound:
            await ctx.send("Message not found. Please provide a valid message ID.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to add reactions to this message.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to add reaction: {e}")

async def setup(bot):
    await bot.add_cog(ReactionCog(bot))
