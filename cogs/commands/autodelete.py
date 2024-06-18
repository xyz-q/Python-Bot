import discord
from discord.ext import commands
import json
import os
import asyncio

AUTO_DELETE_FILE = "auto_delete.json"
ORIGINAL_NAME = "xyz"

class AutoDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_delete_enabled = self.load_auto_delete_status()

    def load_auto_delete_status(self):
        try:
            with open(AUTO_DELETE_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return False

    def save_auto_delete_status(self):
        with open(AUTO_DELETE_FILE, "w") as f:
            json.dump(self.auto_delete_enabled, f)

    @commands.command()
    async def autodelete(self, ctx):
        self.auto_delete_enabled = not self.auto_delete_enabled
        await ctx.send(f"Auto-delete commands {'enabled' if self.auto_delete_enabled else 'disabled'}.")
        self.save_auto_delete_status()
        await self.update_bot_username(ctx)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if self.auto_delete_enabled:
            try:
                await ctx.message.delete()
                await asyncio.sleep(0.5)
                async for message in ctx.channel.history(after=ctx.message.created_at):
                    if message.author == self.bot.user:
                        await message.delete()
                    else:
                        break
            except discord.Forbidden:
                print("Bot doesn't have permission to delete messages.")

        await self.update_bot_username(ctx)

    async def update_bot_username(self, ctx):
        new_nickname = f" 🗑️ {ORIGINAL_NAME} ️" if self.auto_delete_enabled else ORIGINAL_NAME
        try:
            for guild in self.bot.guilds:
                await guild.me.edit(nick=new_nickname)
        except discord.HTTPException as e:
            print(f"Failed to update bot's nickname: {e}")

async def setup(bot):
    await bot.add_cog(AutoDelete(bot))