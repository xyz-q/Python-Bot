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

        msg = await ctx.send("running deploy...")

        process = subprocess.run(
            ["bash", "/home/matty0/bot/Python-Bot/deploy.sh"],
            capture_output=True,
            text=True
        )

        duration = round(time.time() - start, 2)

        output = process.stdout + "\n" + process.stderr

        status = "unknown"
        before = "unknown"
        after = "unknown"
        changed = []

        for line in output.splitlines():
            if "STATUS=" in line:
                status = line.split("=", 1)[1].strip()

            if "BEFORE=" in line:
                before = line.split("=", 1)[1].strip()

            if "AFTER=" in line:
                after = line.split("=", 1)[1].strip()

            if line.startswith("CHANGED_FILES="):
                changed = line.split("=", 1)[1].strip().split()

        embed = discord.Embed()

        embed.title = "deploy"
        embed.color = discord.Color.green() if status == "SUCCESS" else discord.Color.red()

        embed.add_field(name="status", value=status, inline=False)
        embed.add_field(name="commit", value=f"{before[:7]} → {after[:7]}", inline=False)

        if changed:
            embed.add_field(
                name="files changed",
                value="\n".join(changed[:15]),
                inline=False
            )

        embed.add_field(name="time", value=f"{duration}s", inline=False)

        if process.returncode != 0:
            err = (process.stderr or "no stderr").strip()
            embed.add_field(name="error", value=f"```{err[-1500:]}```", inline=False)

        await msg.edit(content=None, embed=embed)


async def setup(bot):
    await bot.add_cog(Deploy(bot))