import discord
from discord.ext import commands
import aiohttp

class EmojiCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def emojiadd(self, ctx, emoji_name: str, emoji_url: str):
        """Command to add a new custom emoji to the server."""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(emoji_url) as resp:
                        if resp.status != 200:
                            return await ctx.send('Failed to fetch image.')

                        emoji_bytes = await resp.read()
                        await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_bytes)
                        await ctx.send(f'Emoji `{emoji_name}` created successfully!')
                except aiohttp.ClientError as e:
                    await ctx.send(f'Failed to create emoji: {e}')
                except discord.HTTPException as e:
                    await ctx.send(f'Failed to create emoji: {e}')

    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    async def emojiremove(self, ctx, emoji_name: str):
        """Command to remove a custom emoji from the server."""
        try:
            emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name)
            if emoji:
                await emoji.delete()
                await ctx.send(f'Emoji `{emoji_name}` has been removed.')
            else:
                await ctx.send(f'Emoji `{emoji_name}` not found in the server.')
        except discord.Forbidden:
            await ctx.send('I do not have permission to manage emojis.')
        except discord.HTTPException as e:
            await ctx.send(f'Failed to remove emoji: {e}')

    @commands.command()
    async def emoji(self, ctx, emoji_name: str):
        """Command to get information about a custom emoji."""
        emoji = discord.utils.get(self.bot.emojis, name=emoji_name)
        if emoji:
            emoji_details = f'Emoji Name: {emoji.name}\nEmoji ID: {emoji.id}\nURL: {emoji.url}'
            await ctx.send(f'```{emoji_details}```')
        else:
            await ctx.send(f'Emoji `{emoji_name}` not found.')

    @commands.command()
    async def emojis(self, ctx):
        emoji_list = []
        sorted_emojis = sorted(ctx.guild.emojis, key=lambda x: x.id, reverse=True)
        
        for emoji in sorted_emojis:
            if emoji.animated:
                raw_format = f"`<a:{emoji.name}:{emoji.id}>`"
            else:
                raw_format = f"`<:{emoji.name}:{emoji.id}>`"
            emoji_format = f"{emoji} - {raw_format}"
            emoji_list.append(emoji_format)
        
        if not emoji_list:
            await ctx.send("This server has no custom emojis!")
            return

        chunks = [emoji_list[i:i + 10] for i in range(0, len(emoji_list), 10)]
        
        for chunk in chunks:
            await ctx.send('\n'.join(chunk))





async def setup(bot):
    await bot.add_cog(EmojiCommands(bot))
