import subprocess
import discord
from discord.ext import commands
import time

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return

        start = time.time()

        msg = await ctx.send("Deploying...")

        process = subprocess.run(
            ["bash", "/home/matty0/bot/Python-Bot/deploy.sh"],
            capture_output=True,
            text=True
        )

        duration = round(time.time() - start, 2)
        output = (process.stdout or "") + "\n" + (process.stderr or "")

        before = None
        after = None
        changed = []
        service_status = "unknown"
        health = "unknown"

        for line in output.splitlines():
            if line.startswith("BEFORE="):
                before = line.split("=", 1)[1].strip()

            if line.startswith("AFTER="):
                after = line.split("=", 1)[1].strip()

            if line.startswith("CHANGED_FILES="):
                changed = line.split("=", 1)[1].strip().split()

            if "SERVICE_STATUS=" in line:
                service_status = line.split("=", 1)[1].strip()

            if "HEALTH=OK" in line:
                health = "OK"

            if "HEALTH=FAILED" in line:
                health = "FAILED"

        # fallback safety
        before = before or "unknown"
        after = after or "unknown"

        if before == after:
            status = "NO_CHANGE"
        else:
            status = "UPDATED"

        embed = discord.Embed(
            title="Deploy Report",
            color=discord.Color.green() if status == "UPDATED" else discord.Color.light_grey()
        )

        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Health Check", value=health, inline=False)
        embed.add_field(name="Commit", value=f"`{before[:7]}` → `{after[:7]}`", inline=False)

        embed.add_field(
            name="Files Changed",
            value="\n".join(changed[:10]) if changed else "None",
            inline=False
        )

        embed.add_field(name="Service", value=service_status, inline=False)
        embed.add_field(name="Time", value=f"{duration}s", inline=False)

        if process.returncode != 0:
            embed.add_field(
                name="Error",
                value=f"```{(process.stderr or 'no error output')[-1500:]}```",
                inline=False
            )

        await msg.edit(content=None, embed=embed)


async def setup(bot):
    await bot.add_cog(Deploy(bot))