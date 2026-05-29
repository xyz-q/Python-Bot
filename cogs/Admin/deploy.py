import discord
from discord.ext import commands
import asyncio
import time

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deploy(self, ctx):
        # 1. Security check (Only your ID can run this)
        if ctx.author.id != 110927272210354176:
            return

        start = time.time()
        msg = await ctx.send("Deploying...")

        # 2. Asynchronously execute bash script with a 45-second safety timeout
        try:
            process = await asyncio.create_subprocess_exec(
                "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45.0)
            output = (stdout.decode() or "") + "\n" + (stderr.decode() or "")
            
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            return await msg.edit(content="❌ **Deployment Timed Out!** The bash script hung for over 45 seconds.")
        except Exception as e:
            return await msg.edit(content=f"❌ **Error executing script:** {e}")

        # 3. Parse Output Lines Cleanly
        before = None
        after = None
        status = "UNKNOWN"
        changed = []

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("BEFORE="):
                before = line.split("=", 1)[1]
            elif line.startswith("AFTER="):
                after = line.split("=", 1)[1]
            elif line.startswith("CHANGED_FILES="):
                parts = line.split("=", 1)
                if len(parts) > 1:
                    changed = parts[1].split()
            elif "NO_CHANGE" in line:
                status = "NO_CHANGE"
            elif "UPDATED" in line:
                status = "UPDATED"
            elif "FETCH_FAILED" in line:
                status = "FETCH_FAILED"

        before = before or "unknown"
        after = after or "unknown"

        # 4. Color setting based on status
        if status == "UPDATED":
            embed_color = discord.Color.green()
        elif status == "NO_CHANGE":
            embed_color = discord.Color.greyple()
        else:
            embed_color = discord.Color.red()

        # 5. Build and send Report Embed
        embed = discord.Embed(title="Deploy Report", color=embed_color)
        embed.add_field(name="status", value=status, inline=False)
        embed.add_field(name="commit", value=f"`{before[:7]}` → `{after[:7]}`", inline=False)
        
        if changed:
            embed.add_field(name="files changed", value="\n".join(changed[:10]), inline=False)
        else:
            embed.add_field(name="files changed", value="None", inline=False)
            
        embed.add_field(name="time", value=f"{round(time.time() - start, 2)}s", inline=False)

        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Deploy(bot))
