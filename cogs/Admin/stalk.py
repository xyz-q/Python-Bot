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
                    user_id = data.get('user_id')
                    self.stalked_user_id = str(user_id) if user_id is not None else None

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

        if self.stalked_user_id:
            stalked_user = self.bot.get_user(int(self.stalked_user_id))
            message = await ctx.send(f"Already stalking {stalked_user.display_name}. Use `,stopstalk` first!")
            await asyncio.sleep(3)
            await message.delete()
            return

        self.stalked_user_id = str(member.id)
        self.save_stalked_user()

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
        if not self.stalked_user_id or self.stalked_user_id == 'None':
            return

        try:
            for guild in self.bot.guilds:
                stalked_user = guild.get_member(int(self.stalked_user_id))
                
                if stalked_user and stalked_user.voice and stalked_user.voice.channel:
                    target_channel = stalked_user.voice.channel
                    
                    # Force reconnect if not in the right channel
                    if not guild.voice_client:
                        try:
                            await target_channel.connect()
                        except:
                            continue
                    elif guild.voice_client.channel != target_channel:
                        try:
                            await guild.voice_client.disconnect()
                            await target_channel.connect()
                        except:
                            continue

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
