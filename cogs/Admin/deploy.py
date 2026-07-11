import discord
from discord.ext import commands
import asyncio
import time
import json
import os

STATE_FILE = "/home/matty0/bot/Python-Bot/deploy_state.json"
OWNER_ID = 110927272210354176

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

            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Bot came back online successfully.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value="✅ Updated & Online", inline=True)
            embed.add_field(name="Total Time", value=f"{total_time}s", inline=True)
            embed.set_footer(text="Deploy System")

            await msg.edit(content=None, embed=embed)
            print("[DEPLOY LOG] Discord message updated successfully post-restart.")

        except Exception as e:
            print(f"[DEPLOY CRASH] Failure inside on_ready recovery loop: {e}")

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != OWNER_ID:
            return

        start_time = time.time()
        embed = discord.Embed(
            title="🚀 Deploy Report",
            description="Running deploy script...",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Status", value="⏳ Deploying", inline=False)
        msg = await ctx.send(embed=embed)

        # 1. Execute the bash script and check its exit code
        try:
            process = await asyncio.create_subprocess_exec(
                "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Deploy script timed out.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value="❌ Timed out after 30s", inline=False)
            return await msg.edit(content=None, embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Failed to launch deploy script.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value=f"❌ {e}", inline=False)
            return await msg.edit(content=None, embed=embed)

        # 2. Abort if the script itself failed - do NOT restart into broken code
        if process.returncode != 0:
            error_output = (stderr.decode(errors="ignore") or stdout.decode(errors="ignore") or "No output").strip()
            if len(error_output) > 1000:
                error_output = error_output[-1000:]
            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Deploy script exited with an error. Restart aborted.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value=f"❌ Exit code {process.returncode}", inline=False)
            embed.add_field(name="Output", value=f"```{error_output}```", inline=False)
            return await msg.edit(content=None, embed=embed)

        # 3. Write the state file so on_ready can pick this up post-restart
        try:
            state_data = {
                "channel_id": int(ctx.channel.id),
                "message_id": int(msg.id),
                "start_time": float(start_time)
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state_data, f, indent=4)
        except Exception as json_err:
            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Script succeeded but failed to persist restart state.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value=f"❌ {json_err}", inline=False)
            return await msg.edit(content=None, embed=embed)

        # 4. Transition message to "restarting" state
        try:
            embed = discord.Embed(
                title="🚀 Deploy Report",
                description="Script succeeded, restarting service now...",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Status", value="🔄 Restarting", inline=True)
            embed.add_field(name="Elapsed", value=f"{round(time.time() - start_time, 2)}s", inline=True)
            await msg.edit(content=None, embed=embed)
        except Exception as embed_err:
            return await ctx.send(f"❌ ERROR: Failed sending intermediate embed: {embed_err}")

        # Pause to let the network packet clear before systemd kills the process
        await asyncio.sleep(2.0)

        # 5. Trigger the background systemctl restart invocation
        try:
            await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")
        except Exception as service_err:
            return await ctx.send(f"❌ ERROR: Failed triggering systemctl restart: {service_err}")

async def setup(bot):
    await bot.add_cog(Deploy(bot))