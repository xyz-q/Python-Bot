import discord
from discord.ext import commands
import re
import discord
from discord.ext import commands
import re
from typing import List
import asyncio

class DMCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dm')
    @commands.has_permissions(administrator=True) 
    async def dm(self, ctx, user_reference: str, *, message: str):
        # Delete the command message immediately
        await ctx.message.delete()
        
        user = None

        mention_match = re.match(r'<@!?(\d+)>', user_reference)
        if mention_match:
            user_id = int(mention_match.group(1))
            user = await self.bot.fetch_user(user_id)
        else:
            try:
                user_id = int(user_reference)
                user = await self.bot.fetch_user(user_id)
            except ValueError:
                user = discord.utils.get(ctx.guild.members, name=user_reference)

        if user:
            try:
                await user.send(message)
                # Send confirmation and delete it after 5 seconds
                confirmation = await ctx.send(f"Successfully sent a DM to {user.name}.")
                await confirmation.delete(delay=5)
            except discord.Forbidden:
                error_msg = await ctx.send("I do not have permission to send a DM to this user.")
                await error_msg.delete(delay=5)
            except discord.HTTPException as e:
                error_msg = await ctx.send(f"Failed to send DM: {e}")
                await error_msg.delete(delay=5)
        else:
            error_msg = await ctx.send("User not found.")
            await error_msg.delete(delay=5)

    @dm.error
    async def dm_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            error_msg = await ctx.send("You need administrator permissions to use this command.")
            await error_msg.delete(delay=5)
            # Also delete the command message if possible
            try:
                await ctx.message.delete()
            except:
                pass


    @commands.command(name='dms')
    @commands.has_permissions(administrator=True)
    async def dms(self, ctx, user_reference: str):
        user = None

        mention_match = re.match(r'<@!?(\d+)>', user_reference)
        if mention_match:
            user_id = int(mention_match.group(1))
            user = await self.bot.fetch_user(user_id)
        else:
            try:
                user_id = int(user_reference)
                user = await self.bot.fetch_user(user_id)
            except ValueError:
                user = discord.utils.get(ctx.guild.members, name=user_reference)
                if not user:
                    user = discord.utils.get(ctx.guild.members, display_name=user_reference)

        if user:
            try:
                dm_channel = await user.create_dm()
                messages = []
                async for message in dm_channel.history(limit=10):
                    messages.append(message)

                if messages:
                    history = "\n".join(
                        [f"{message.created_at} - {message.author}: {message.content}" for message in messages])
                    await ctx.send(f"DM history with {user.name}:\n{history}")
                else:
                    await ctx.send(f"No recorded DMs with {user.name}.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to view DMs with this user.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to fetch DMs: {e}")
        else:
            await ctx.send("User not found.")

    @dms.error
    async def dms_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")



async  def setup(bot):
    await bot.add_cog(DMCommands(bot))
