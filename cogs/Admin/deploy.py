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
    """Safely writes a structured log entry into the file system history ledger."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        b_str = str(before)[:7]
        a_str = str(after)[:7]
        f_str = ", ".join(files_changed) if files_changed else "None"
        
        log_entry = f"[{timestamp}] STATUS: {status} | COMMIT: {b_str} -> {a_str} | FILES: {f_str} | DURATION: {elapsed_time}s\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
        return True
    except Exception as log_error:
        print(f"[Deploy Log Error] Failed to write log: {log_error}")
        return False

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Triggers immediately when the bot establishes an initial connection."""
        await self.check_pending_deploy()

    async def check_pending_deploy(self):
        """Resumes a pending deploy state with connection retry metrics inside the embed."""
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            os.remove(STATE_FILE)

            # Wait until internal channel/server cache is ready
            await self.bot.wait_until_ready()

            channel = None
            msg = None
            max_retries = 5
            retry_delay = 3.0
            attempts_taken = 0

            # Connection Retry Loop
            for attempt in range(1, max_retries + 1):
                attempts_taken = attempt
                try:
                    channel = await self.bot.fetch_channel(state["channel_id"])
                    if channel:
                        msg = await channel.fetch_message(state["message_id"])
                        if msg:
                            break
                except Exception as fetch_err:
                    print(f"[Deploy Warning] Fetch attempt {attempt}/{max_retries} failed: {fetch_err}")
                
                await asyncio.sleep(retry_delay * attempt)

            if not msg:
                log_deployment("ERROR_CONTEXT_LOST", state["before"], state["after"], state["changed"], 0)
                return

            total_time = round(time.time() - state["start_time"], 2)

            # Write data log to disk file
            log_success = log_deployment("UPDATED (ONLINE)", state["before"], state["after"], state["changed"], total_time)
            log_status_text = "SUCCESSFUL (deploy_history.log)" if log_success else "FAILED"

            # Compile production report embed containing real-time retry metrics
            embed = discord.Embed(title="Deploy Report", color=discord.Color.green())
            embed.add_field(name="status", value="UPDATED (ONLINE)", inline=False)
            embed.add_field(name="commit", value=f"`{state['before'][:7]}` -> `{state['after'][:7]}`", inline=False)
            
            if state["changed"]:
                embed.add_field(name="files changed", value="\n".join(state["changed"][:10]), inline=False)
            else:
                embed.add_field(name="files changed", value="None", inline=False)
                
            embed.add_field(name="connection checks", value=f"{attempts_taken} / {max_retries} attempts", inline=False)
            embed.add_field(name="logging status", value=log_status_text, inline=False)
            embed.add_field(name="time", value=f"{total_time}s (Total Reload)", inline=False)

            await msg.edit(content=None, embed=embed)

        except Exception as e:
            print(f"[Deploy Error] Execution context failure in pending deploy recovery: {e}")

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
            
            before = "unknown"
            after = "unknown"
            status = "UNKNOWN"
            changed = []

            for line in output.splitlines():
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    if key == "BEFORE":
                        before = value
                    elif key == "AFTER":
                        after = value
                    elif key == "CHANGED_FILES":
                        changed = value.split()
                        
                if "NO_CHANGE" in line:
                    status = "NO_CHANGE"
                elif "UPDATED" in line:
                    status = "UPDATED"
                elif "FETCH_FAILED" in line:
                    status = "FETCH_FAILED"

            if status != "UPDATED":
                total_time = round(time.time() - start_time, 2)
                log_success = log_deployment(status, before, after, changed, total_time)
                log_status_text = "SUCCESSFUL (deploy_history.log)" if log_success else "FAILED"
                
                embed_color = discord.Color.greyple() if status == "NO_CHANGE" else discord.Color.red()
                embed = discord.Embed(title="Deploy Report", color=embed_color)
                embed.add_field(name="status", value=status, inline=False)
                embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
                embed.add_field(name="files changed", value="None", inline=False)
                embed.add_field(name="logging status", value=log_status_text, inline=False)
                embed.add_field(name="time", value=f"{total_time}s", inline=False)
                return await msg.edit(content=None, embed=embed)

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
            log_deployment(f"CRASH: {str(e)}", "unknown", "unknown", [], total_time)
            return await msg.edit(content=f"ERROR: Execution failed: {e}")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
