from discord.ext import commands, tasks
import discord
import asyncio

default_status = discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/jJ8QcTB3")
dnd_activity = discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/VGucfdymCm")
idle_activity = discord.Activity(type=discord.ActivityType.listening, name="@.zxpq")

class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_dnd = True 

    @commands.command()
    async def resetstatus(self, ctx):
        await self.bot.change_presence(activity=default_status)
        await ctx.send("Status reset to default.")

    @commands.command()
    async def dnd(self, ctx):
        self.is_dnd = not self.is_dnd 
        if self.is_dnd:
            await self.bot.change_presence(status=discord.Status.dnd, activity=dnd_activity)
            await ctx.send("Bot status set to Do Not Disturb.")
            print("\033[91mBot is now in Do Not Disturb mode.\033[0m")
        else:
            await self.bot.change_presence(status=discord.Status.idle, activity=idle_activity)
            await ctx.send("Bot status set to Idle.")
            print("\033[33mBot is now in Idle mode.\033[0m")

    @commands.command()
    async def online(self, ctx):
        await self.bot.change_presence(status=discord.Status.online)
        await ctx.send("Bot status set to Online.")
        print("\033[92mBot is now in Online mode.\033[0m")

    @commands.command()
    async def offline(self, ctx):
        await self.bot.change_presence(status=discord.Status.offline)
        await ctx.send("Bot is now appearing offline.")
        print("Bot is now appearing offline")

    @commands.command()
    async def setstatus(self, ctx, activity_type: str, *, status: str):
        activity_type = activity_type.lower()
        if activity_type not in ["playing", "listening", "watching", "streaming"]:
            await ctx.send("Invalid activity type. Please choose from: playing, listening, watching, streaming.")
            return

        if not status:
            await ctx.send("Please provide a <status>.")
            return

        activity_type_enum = discord.ActivityType.playing
        if activity_type == "listening":
            activity_type_enum = discord.ActivityType.listening
        elif activity_type == "watching":
            activity_type_enum = discord.ActivityType.watching
        elif activity_type == "streaming":
            activity_type_enum = discord.ActivityType.streaming

        await self.bot.change_presence(activity=discord.Activity(type=activity_type_enum, name=status))
        await ctx.send(f"Status changed to '[{activity_type.capitalize()}] [{status}]'")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.is_dnd:
            await self.bot.change_presence(status=discord.Status.dnd, activity=dnd_activity)
            await asyncio.sleep(4.5)
            print("\033[91mBot is now in Do Not Disturb mode.\033[0m")

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))
