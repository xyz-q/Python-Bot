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
        """Loads the JSON file and updates the exact deployment message left hanging."""
        if not os.path.exists(STATE_FILE):
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            # Immediately delete the state file to prevent boot loops
            os.remove(STATE_FILE)

            # Force the bot to wait until its channel cache is fully available
            await self.bot.wait_until_ready()

            channel = await self.bot.fetch_channel(state["channel_id"])
            msg = await channel.fetch_message(state["message_id"])
            
            total_time = round(time.time() - state["start_time"], 2)

            # Finalize the report card to green
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

        before = "unknown"
        after = "unknown"
        status = "UNKNOWN"
        changed = []

        try:
            # 1. Fire off the subprocess bash script
            process = await asyncio.create_subprocess_exec(
                "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            output = (stdout.decode() or "") + "\n" + (stderr.decode() or "")
            
            # 2. Bulletproof String Processing Engine (No array splits that cause index errors)
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("BEFORE="):
                    before = line.replace("BEFORE=", "", 1)
                elif line.startswith("AFTER="):
                    after = line.replace("AFTER=", "", 1)
                elif line.startswith("CHANGED_FILES="):
                    changed = line.replace("CHANGED_FILES=", "", 1).split()
                
                if "NO_CHANGE" in line:
                    status = "NO_CHANGE"
                elif "UPDATED" in line:
                    status = "UPDATED"

            # 3. Handle early terminations immediately if no changes are detected
            if status != "UPDATED":
                embed_color = discord.Color.greyple() if status == "NO_CHANGE" else discord.Color.red()
                embed = discord.Embed(title="Deploy Report", color=embed_color)
                embed.add_field(name="status", value=status, inline=False)
                embed.add_field(name="commit", value=f"`{before[:7]}` -> `{after[:7]}`", inline=False)
                embed.add_field(name="files changed", value="None", inline=False)
                embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
                return await msg.edit(content=None, embed=embed)

        except Exception as e:
            # If the subprocess engine throws any kind of unexpected fault, report it cleanly
            return await msg.edit(content=f"ERROR: Framework execution failed: {e}")

        # 4. Save tracking state configuration data down to disk space
        state_data = {
            "channel_id": ctx.channel.id,
            "message_id": msg.id,
            "before": str(before),
            "after": str(after),
            "status": status,
            "changed": changed,
            "start_time": start_time
        }
        
        with open(STATE_FILE, "w") as f:
            json.dump(state_data, f, indent=4)

        # 5. Shift embed profile layout to orange pending state
        embed = discord.Embed(title="Deploy Report", color=discord.Color.orange())
        embed.add_field(name="status", value="RESTARTING (APPLYING CHANGES)", inline=False)
        embed.add_field(name="commit", value=f"`{str(before)[:7]}` -> `{str(after)[:7]}`", inline=False)
        embed.add_field(name="time", value=f"{round(time.time() - start_time, 2)}s", inline=False)
        
        await msg.edit(content=None, embed=embed)
        
        # Buffer packet release delay
        await asyncio.sleep(2.0)

        # 6. Issue systemctl background instance restart invocation
        await asyncio.create_subprocess_exec("sudo", "/bin/systemctl", "restart", "discord-bot.service")

async def setup(bot):
    await bot.add_cog(Deploy(bot))
