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
        """Automatically checks for a pending deployment state on boot."""
        await self.check_pending_deploy()

    async def check_pending_deploy(self):
        """Finalizes the deployment report after a successful systemd restart."""
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            # Clean up the state file immediately
            os.remove(STATE_FILE)

            # Resolve the original Discord context
            channel = self.bot.get_channel(state["channel_id"])
            if not channel:
                channel = await self.bot.fetch_channel(state["channel_id"])
            
            msg = await channel.fetch_message(state["message_id"])
            total_time = round(time.time() - state["start_time"], 2)

            # Build the final success report
            embed = discord.Embed(title="Deploy Report", color=discord.Color.green())
            embed.add_field(name="status", value="UPDATED (ONLINE)", inline=False)
            embed.add_field(name="commit", value=f"`{state['before'][:7]}` -> `{state['after'][:7]}`", inline=False)
            
            if state["changed"]:
                embed.add_field(name="files changed", value="\n".join(state["changed"][:10]), inline=False)
            else:
                embed.add_field(name="files changed", value="None", inline=False)
                
            embed.add_field(name="time", value=f"{total_time}s (Total Reload)", inline=False)

            await msg.edit(content=None, embed=embed)

        except Exception as e:
            print(f"[Deploy Error] Failed to resume deployment state: {e}")

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return

        start_time = time.time()
        msg = await ctx.send("Deploying...")

        try:
            # 1. Run the background deployment shell script
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

            # 2. Parse output strings (FIXED: Restored correct [1] indexers)
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

            # 3. Handle non-updating states immediately without restarting
            if status != "UPDATED":
                embed_color = discord.Color.greyple() if status == "NO_CHANGE" else discord.Color.red()
                embed = discord.Embed(title="Deploy Report", color=embed_color)
                embed.add_field(name="status", value=status, inline=False)
                embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
                embed.add_field(name="files changed", value="None", inline=False)
                embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
                return await msg.edit(content=None, embed=embed)

            # 4. Save clean serialization state data
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

            # 5. Output intermediate status card
            embed = discord.Embed(title="Deploy Report", color=discord.Color.orange())
            embed.add_field(name="status", value="RESTARTING (APPLYING CHANGES)", inline=False)
            embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
            embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
            await msg.edit(content=None, embed=embed)
            
            # Network clear buffer
            await asyncio.sleep(2.0)

            # 6. Issue systemd background flush restart
            await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")

        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return await msg.edit(content="ERROR: Deployment Timed Out (Script exceeded 45 seconds).")
        except Exception as e:
            return await msg.edit(content=f"ERROR: Execution failed: {e}")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
