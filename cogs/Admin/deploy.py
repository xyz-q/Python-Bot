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
        """Triggers automatically on boot to check for a pending deployment message."""
        await self.check_pending_deploy()

    async def check_pending_deploy(self):
        """Loads the JSON file and updates the exact deployment message that was left hanging."""
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            # Immediately delete the file so it doesn't loop on future restarts
            os.remove(STATE_FILE)

            # Wait for internal Discord caches to load completely
            await self.bot.wait_until_ready()

            # Find the exact channel and message from the saved state data
            channel = await self.bot.fetch_channel(state["channel_id"])
            msg = await channel.fetch_message(state["message_id"])
            
            total_time = round(time.time() - state["start_time"], 2)

            # Edit the original message to show the final successful status
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
            # 1. Execute the bash script
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

            # 2. Fixed, bulletproof output parser using exact string values
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("BEFORE="):
                    before = line.split("BEFORE=", 1)[1]
                elif line.startswith("AFTER="):
                    after = line.split("AFTER=", 1)[1]
                elif line.startswith("CHANGED_FILES="):
                    changed = line.split("CHANGED_FILES=", 1)[1].split()
                
                if "NO_CHANGE" in line:
                    status = "NO_CHANGE"
                elif "UPDATED" in line:
                    status = "UPDATED"

            # 3. If there are no updates, finish right here without restarting
            if status != "UPDATED":
                embed_color = discord.Color.greyple() if status == "NO_CHANGE" else discord.Color.red()
                embed = discord.Embed(title="Deploy Report", color=embed_color)
                embed.add_field(name="status", value=status, inline=False)
                embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
                embed.add_field(name="files changed", value="None", inline=False)
                embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
                return await msg.edit(content=None, embed=embed)

            # 4. Save the tracking state data into the JSON file
            state_data = {
                "channel_id": ctx.channel.id,
                "message_id": msg.id,         # Remembers the exact message to edit later
                "before": str(before),
                "after": str(after),
                "status": status,
                "changed": changed,
                "start_time": start_time
            }
            
            with open(STATE_FILE, "w") as f:
                json.dump(state_data, f, indent=4)

            # 5. Flip the embed status to intermediate "RESTARTING"
            embed = discord.Embed(title="Deploy Report", color=discord.Color.orange())
            embed.add_field(name="status", value="RESTARTING (APPLYING CHANGES)", inline=False)
            embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
            embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
            
            await msg.edit(content=None, embed=embed)
            
            # Give Discord a brief window to process the network request before the bot drops offline
            await asyncio.sleep(2.0)

            # 6. Execute systemd process bounce
            await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")

        except Exception as e:
            return await msg.edit(content=f"ERROR: Execution failed: {e}")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
