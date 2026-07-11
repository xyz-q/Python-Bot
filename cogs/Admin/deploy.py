import discord
from discord.ext import commands
import asyncio
import time
import json
import os

STATE_FILE = "/home/matty0/bot/Python-Bot/deploy_state.json"
REPO_DIR = "/home/matty0/bot/Python-Bot"
OWNER_ID = 110927272210354176


def build_embed(status, description, color, fields=None, footer_extra=None):
    embed = discord.Embed(
        title="Deploy Report",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Status", value=status, inline=False)
    for name, value, inline in (fields or []):
        embed.add_field(name=name, value=value, inline=inline)
    footer = "Deploy System" + (f" · {footer_extra}" if footer_extra else "")
    embed.set_footer(text=footer)
    return embed


async def get_git_commit():
    """Returns the current short commit hash for REPO_DIR, or None on failure"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--short", "HEAD",
            cwd=REPO_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        if proc.returncode == 0:
            return out.decode(errors="ignore").strip()
    except Exception:
        pass
    return None


class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Attempts to recover context on boot with explicit console error logging."""
        if not os.path.exists(STATE_FILE):
            return

        print("[DEPLOY LOG] State file found on boot. Attempting recovery...")
        state = None
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            os.remove(STATE_FILE)
            await self.bot.wait_until_ready()

            channel = await self.bot.fetch_channel(int(state["channel_id"]))
            msg = await channel.fetch_message(int(state["message_id"]))
            total_time = round(time.time() - float(state["start_time"]), 2)

            embed = build_embed(
                status="Online",
                description="Deployment complete. Bot has restarted successfully.",
                color=discord.Color.green(),
                fields=[
                    ("Git", state.get("git_status", "Unknown"), True),
                    ("Total time", f"{total_time}s", True)
                ]
            )

            await msg.edit(content=None, embed=embed)
            print("[DEPLOY LOG] Discord message updated successfully post-restart.")

        except Exception as e:
            print(f"[DEPLOY CRASH] Failure inside on_ready recovery loop: {e}")
            if state:
                try:
                    channel = await self.bot.fetch_channel(int(state["channel_id"]))
                    await channel.send(f"Bot restarted, but the deploy message couldn't be updated: {e}")
                except Exception:
                    pass

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != OWNER_ID:
            return

        start_time = time.time()
        commit_before = await get_git_commit()
        embed = build_embed(
            status="Running deploy script",
            description="Pulling latest changes and installing updates.",
            color=discord.Color.blurple()
        )
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
            embed = build_embed(
                status="Timed out",
                description="The deploy script did not finish within 30 seconds.",
                color=discord.Color.red()
            )
            return await msg.edit(content=None, embed=embed)
        except Exception as e:
            embed = build_embed(
                status="Failed to launch",
                description="The deploy script could not be started.",
                color=discord.Color.red(),
                fields=[("Error", str(e), False)]
            )
            return await msg.edit(content=None, embed=embed)

        # 2. Abort if the script itself failed - do NOT restart into broken code
        if process.returncode != 0:
            error_output = (stderr.decode(errors="ignore") or stdout.decode(errors="ignore") or "No output").strip()
            if len(error_output) > 1000:
                error_output = error_output[-1000:]
            embed = build_embed(
                status="Script error — restart aborted",
                description="The deploy script exited with an error, so the restart was skipped.",
                color=discord.Color.red(),
                fields=[
                    ("Exit code", str(process.returncode), True),
                    ("Output", f"```{error_output}```", False)
                ]
            )
            return await msg.edit(content=None, embed=embed)

        # 3. Write the state file so on_ready can pick this up post-restart
        commit_after = await get_git_commit()
        git_changed = bool(commit_before and commit_after and commit_before != commit_after)
        if commit_before and commit_after:
            git_status = f"Updated ({commit_before} → {commit_after})" if git_changed else f"No changes ({commit_after})"
        else:
            git_status = "Unknown (couldn't read git commit)"

        try:
            state_data = {
                "channel_id": int(ctx.channel.id),
                "message_id": int(msg.id),
                "start_time": float(start_time),
                "git_status": git_status
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state_data, f, indent=4)
        except Exception as json_err:
            embed = build_embed(
                status="Failed to save restart state",
                description="The script ran successfully, but the restart could not be tracked.",
                color=discord.Color.red(),
                fields=[("Error", str(json_err), False)]
            )
            return await msg.edit(content=None, embed=embed)

        # 4. Transition message to "restarting" state
        try:
            embed = build_embed(
                status="Restarting service",
                description="Script completed successfully. Restarting the bot process now.",
                color=discord.Color.orange(),
                fields=[
                    ("Git", git_status, True),
                    ("Elapsed", f"{round(time.time() - start_time, 2)}s", True)
                ]
            )
            await msg.edit(content=None, embed=embed)
        except Exception as embed_err:
            return await ctx.send(f"Failed to update the deploy message: {embed_err}")

        # Pause to let the network packet clear before systemd kills the process
        await asyncio.sleep(2.0)

        # 5. Trigger the systemctl restart and verify it was actually accepted
        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "/bin/systemctl", "restart", "discord-bot.service", "--no-block",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                # If the restart actually succeeds, systemd kills this process
                # partway through this wait and none of the code below runs.
                # We only get here if the restart command failed fast (bad perms, etc).
                out, err = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                if proc.returncode != 0:
                    if os.path.exists(STATE_FILE):
                        os.remove(STATE_FILE)
                    error_output = (err.decode(errors="ignore") or out.decode(errors="ignore") or "Unknown error").strip()
                    embed = build_embed(
                        status="Restart rejected",
                        description="The restart command was rejected. The bot is still running the old process.",
                        color=discord.Color.red(),
                        fields=[
                            ("systemctl exit code", str(proc.returncode), True),
                            ("Output", f"```{error_output[-1000:]}```", False)
                        ]
                    )
                    await msg.edit(content=None, embed=embed)
            except asyncio.TimeoutError:
                # Taking a while to stop/start is normal, on_ready will finish the report
                pass
        except Exception as service_err:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            embed = build_embed(
                status="Failed to trigger restart",
                description="The restart command could not be run.",
                color=discord.Color.red(),
                fields=[("Error", str(service_err), False)]
            )
            return await msg.edit(content=None, embed=embed)


async def setup(bot):
    await bot.add_cog(Deploy(bot))