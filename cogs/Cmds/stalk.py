import discord
from discord.ext import commands, tasks
import asyncio
import json
import os

class Stalk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stalked_user_id = None
        self.load_stalked_user()
        self.follow_user.start()

    def load_stalked_user(self):
        try:
            if os.path.exists('.json/stalked_user.json'):
                with open('.json/stalked_user.json', 'r') as f:
                    data = json.load(f)
                    self.stalked_user_id = str(data.get('user_id'))
                print(f"Loaded stalked user: {self.stalked_user_id}")
        except Exception as e:
            print(f"Error loading stalked user: {e}")
            self.stalked_user_id = None

    def save_stalked_user(self):
        try:
            with open('.json/stalked_user.json', 'w') as f:
                json.dump({'user_id': self.stalked_user_id}, f)
            print(f"Saved stalked user: {self.stalked_user_id}")
        except Exception as e:
            print(f"Error saving stalked user: {e}")

    @commands.command()
    async def stalk(self, ctx, member: discord.Member):
        await ctx.message.delete()

        # Check if already stalking someone
        if self.stalked_user_id:
            stalked_user = self.bot.get_user(int(self.stalked_user_id))
            message = await ctx.send(f"Already stalking {stalked_user.display_name}. Use `,stopstalk` first!")
            await asyncio.sleep(3)
            await message.delete()
            return

        self.stalked_user_id = str(member.id)
        self.save_stalked_user()

        # If they're in a voice channel, connect immediately
        if member.voice:
            try:
                await member.voice.channel.connect(timeout=5)
            except discord.ClientException:
                pass

        message = await ctx.send(f"Now stalking {member.display_name}. I will join their voice channel whenever they connect!")
        await asyncio.sleep(3)
        await message.delete()

    @commands.command(name='stopstalk')
    async def stopstalk(self, ctx):
        await ctx.message.delete()

        if self.stalked_user_id:
            # Disconnect from all voice channels in all guilds
            for guild in self.bot.guilds:
                if guild.voice_client:
                    await guild.voice_client.disconnect()
            
            stalked_user = self.bot.get_user(int(self.stalked_user_id))
            self.stalked_user_id = None
            self.save_stalked_user()
            
            message = await ctx.send(f"Stopped stalking {stalked_user.display_name}.")
            await asyncio.sleep(3)
            await message.delete()
        else:
            notstalking = await ctx.send("The bot is not currently stalking anyone.")
            await asyncio.sleep(3)
            await notstalking.delete()

    @tasks.loop(seconds=0.5)
    async def follow_user(self):
        if not self.stalked_user_id:
            return

        try:
            # Find the user in any guild
            user_found = False
            user_voice_channel = None
            user_guild = None

            for guild in self.bot.guilds:
                member = guild.get_member(int(self.stalked_user_id))
                if member and member.voice:
                    user_found = True
                    user_voice_channel = member.voice.channel
                    user_guild = guild
                    break

            # Disconnect from all guilds where the user isn't present in voice
            for guild in self.bot.guilds:
                if guild.voice_client and (not user_found or guild != user_guild):
                    await guild.voice_client.disconnect()

            # Connect to the user's current voice channel if they're in one
            if user_found and user_voice_channel:
                voice_client = user_guild.voice_client
                if not voice_client:
                    try:
                        await user_voice_channel.connect(timeout=5)
                        print(f"Connected to {user_voice_channel.name} in {user_guild.name}")
                    except discord.ClientException:
                        pass
                elif voice_client.channel != user_voice_channel:
                    try:
                        await voice_client.move_to(user_voice_channel)
                        print(f"Moved to {user_voice_channel.name} in {user_guild.name}")
                    except (discord.ClientException, AttributeError):
                        pass

        except Exception as e:
            print(f"Error in follow_user: {e}")

    @follow_user.before_loop
    async def before_follow_user(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def stalkstatus(self, ctx):
        """Check who is currently being stalked"""
        await ctx.message.delete()
        
        if self.stalked_user_id:
            stalked_user = self.bot.get_user(int(self.stalked_user_id))
            if stalked_user:
                message = await ctx.send(f"Currently stalking: {stalked_user.display_name}")
            else:
                message = await ctx.send("Currently stalking a user, but they seem to be unavailable.")
        else:
            message = await ctx.send("Not currently stalking anyone.")
        
        await asyncio.sleep(3)
        await message.delete()

async def setup(bot):
    await bot.add_cog(Stalk(bot))
