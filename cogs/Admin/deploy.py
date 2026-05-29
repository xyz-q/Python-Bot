import discord
from discord.ext import commands
import asyncio
import time
import json
import os
from datetime import datetime

STATE_FILE = "/home/matty0/bot/Python-Bot/deploy_state.json"
LOG_FILE = "/home/matty0/bot/Python-Bot/deploy_history.log"

def log_deployment(status, before, after, files_changed, elapsed_time):
    """Writes a clean, professional timestamped log entry to the history file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] STATUS: {status} | "
        f"COMMIT: {before[:7]} -> {after[:7]} | "
        f"FILES: {', '.join(files_changed) if files_changed else 'None'} | "
        f"DURATION: {elapsed_time}s\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Automatically checks for a pending deployment state on boot."""
        await self.check_pending_deploy()

    async def check_pending_deploy(self):
        """Finalizes the deployment report and logs the successful reboot."""
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            os.remove(STATE_FILE)

            # Wait until internal channel/server cache is fully ready
            await self.bot.wait_until_ready()

            channel = await self.bot.fetch_channel(state["channel_id"])
            msg = await channel.fetch_message(state["message_id"])
            
            total_time = round(time.time() - state["start_time"], 2)

            embed = discord.Embed(title="Deploy Report", color=discord.Color.green())
            embed.add_field(name="status", value="UPDATED (ONLINE)", inline=False)
            embed.add_field(name="commit", value=f"`{state['before'][:7]}` -> `{state['after'][:7]}`", inline=False)
            
            if state["changed"]:
                embed.add_field(name="files changed", value="\n".join(state["changed"][:10]), inline=False)
            else:
                embed.add_field(name="files changed", value="None", inline=False)
                
            embed.add_field(name="time", value=f"{total_time}s (Total Reload)", inline=False)

            await msg.edit(content=None, embed=embed)
            
            # Log the successful completion post-restart
            log_deployment("UPDATED (ONLINE)", state["before"], state["after"], state["changed"], total_time)

        except Exception as e:
            print(f"[Deploy Error] Failed to resume deployment state: {e}")

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return

        start_time = time.time()
        msg = await ctx.send("Deploying...")

        try:
            process = await asyncio.create_subprocess_exec(
                "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45.0)
            output = (stdout.decode() or "") + "\n" + (stderr.decode() or "")
            
            before = None
            after = None
            status = "UNKNOWN"
            changed = []

            # FIXED: Added indexers [1] to extract strings, allowing .split() to work correctly
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("BEFORE="):
                    before = line.split("=", 1)[1]
                elif line.startswith("AFTER="):
                    after = line.split("=", 1)[1]
                elif line.startswith("CHANGED_FILES="):
                    changed = line.split("=", 1)[1].split()
                elif "NO_CHANGE" in line:
                    status = "NO_CHANGE"
                elif "UPDATED" in line:
                    status = "UPDATED"
                elif "FETCH_FAILED" in line:
                    status = "FETCH_FAILED"

            before = before or "unknown"
            after = after or "unknown"

            # If deployment failed or nothing changed, log it immediately and exit
            if status != "UPDATED":
                total_time = round(time.time() - start_time, 2)
                log_deployment(status, before, after, changed, total_time)
                
                embed_color = discord.Color.greyple() if status == "NO_CHANGE" else discord.Color.red()
                embed = discord.Embed(title="Deploy Report", color=embed_color)
                embed.add_field(name="status", value=status, inline=False)
                embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
                embed.add_field(name="files changed", value="None", inline=False)
                embed.add_field(name="time", value=f"{total_time}s", inline=False)
                return await msg.edit(content=None, embed=embed)

            # If updates found, compile state to JSON
            state_data = {
                "channel_id": ctx.channel.id,
                "message_id": msg.id,
                "before": before,
                "after": after,
                "status": status,
                "changed": changed,
                "start_time": start_time
            }
            
            with open(STATE_FILE, "w") as f:
                json.dump(state_data, f, indent=4)

            embed = discord.Embed(title="Deploy Report", color=discord.Color.orange())
            embed.add_field(name="status", value="RESTARTING (APPLYING CHANGES)", inline=False)
            embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
            embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
            
            await msg.edit(content=None, embed=embed)
            await asyncio.sleep(2.0)

            await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")

        except Exception as e:
            total_time = round(time.time() - start_time, 2)
            log_deployment(f"CRASH_ERROR: {str(e)[:30]}", "unknown", "unknown", [], total_time)
            return await msg.edit(content=f"ERROR: Execution failed: {e}")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
