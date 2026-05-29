import discord
from discord.ext import commands
import asyncio
import time
import json
import os

STATE_FILE = "/home/matty0/bot/Python-Bot/deploy_state.json"

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Attempts to recover context on boot with explicit console error logging."""
        if not os.path.exists(STATE_FILE):
            return

        print("[DEPLOY LOG] State file found on boot. Attempting recovery...")
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            os.remove(STATE_FILE)
            await self.bot.wait_until_ready()

            channel = await self.bot.fetch_channel(int(state["channel_id"]))
            msg = await channel.fetch_message(int(state["message_id"]))
            total_time = round(time.time() - float(state["start_time"]), 2)

            embed = discord.Embed(title="Deploy Report", color=discord.Color.green())
            embed.add_field(name="status", value="UPDATED (ONLINE)", inline=False)
            embed.add_field(name="time", value=f"{total_time}s (Total Reload)", inline=False)

            await msg.edit(content=None, embed=embed)
            print("[DEPLOY LOG] Discord message updated successfully post-restart.")

        except Exception as e:
            print(f"[DEPLOY CRASH] Failure inside on_ready recovery loop: {e}")

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return

        start_time = time.time()
        msg = await ctx.send("Deploying...")

        # 1. Execute the bash script with an explicit timeout error catch
        try:
            process = await asyncio.create_subprocess_exec(
                "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return await msg.edit(content="❌ ERROR: The deployment script timed out after 30 seconds.")
        except Exception as e:
            return await msg.edit(content=f"❌ ERROR: Subprocess failed to execute: {e}")

        # 2. Try writing the JSON state file with explicit error reporting to Discord
        try:
            state_data = {
                "channel_id": int(ctx.channel.id),
                "message_id": int(msg.id),
                "start_time": float(start_time)
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state_data, f, indent=4)
        except Exception as json_err:
            return await msg.edit(content=f"❌ ERROR: Failed writing JSON file to disk: {json_err}")

        # 3. Transition message to orange state
        try:
            embed = discord.Embed(title="Deploy Report", color=discord.Color.orange())
            embed.add_field(name="status", value="RESTARTING (APPLYING CHANGES)", inline=False)
            embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
            await msg.edit(content=None, embed=embed)
        except Exception as embed_err:
            return await ctx.send(f"❌ ERROR: Failed sending intermediate embed: {embed_err}")
        
        # Pause to let the network packet clear before systemd kills the process
        await asyncio.sleep(2.0)

        # 4. Trigger the background systemctl restart invocation
        try:
            await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")
        except Exception as service_err:
            return await ctx.send(f"❌ ERROR: Failed triggering systemctl restart: service_err")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
