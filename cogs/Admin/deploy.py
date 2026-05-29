import subprocess
import discord
from discord.ext import commands
import time
import asyncio

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def run_deploy(self):
        process = subprocess.run(
            ["bash", "/home/matty0/bot/Python-Bot/deploy.sh"],
            capture_output=True,
            text=True
        )
        return process.stdout + "\n" + process.stderr

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return

        start = time.time()

        msg = await ctx.send("running deploy...")

        # 🔥 run in background thread so bot doesn't freeze
        output = await asyncio.to_thread(self.run_deploy)

        duration = round(time.time() - start, 2)

        before = None
        after = None
        changed = []
        status = "unknown"

        for line in output.splitlines():
            if line.startswith("BEFORE="):
                before = line.split("=", 1)[1]

            if line.startswith("AFTER="):
                after = line.split("=", 1)[1]

            if line.startswith("CHANGED_FILES="):
                changed = line.split("=", 1)[1].split()

            if "NO_CHANGE" in line:
                status = "NO_CHANGE"

            if "UPDATED" in line:
                status = "UPDATED"

        before = before or "unknown"
        after = after or "unknown"

        embed = discord.Embed(
            title="deploy",
            color=discord.Color.green() if status == "UPDATED" else discord.Color.greyple()
        )

        embed.add_field(name="status", value=status, inline=False)
        embed.add_field(name="commit", value=f"`{before[:7]}` → `{after[:7]}`", inline=False)
        embed.add_field(name="time", value=f"{duration}s", inline=False)

        if changed:
            embed.add_field(name="files changed", value="\n".join(changed[:10]), inline=False)

        await msg.edit(content=None, embed=embed)