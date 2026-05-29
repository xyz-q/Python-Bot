import discord
from discord.ext import commands
import asyncio # Changed from subprocess
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

        # Run the subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            "bash", "/home/matty0/bot/Python-Bot/deploy.sh",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for the script to finish without freezing the bot
        stdout, stderr = await process.communicate()
        output = (stdout.decode() or "") + "\n" + (stderr.decode() or "")

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
                changed = line.split("=", 1)[1].split()
            elif "NO_CHANGE" in line:
                status = "NO_CHANGE"
            elif "UPDATED" in line:
                status = "UPDATED"

        before = before or "unknown"
        after = after or "unknown"

        embed = discord.Embed(
            title="Deploy Report",
            color=discord.Color.green() if status == "UPDATED" else discord.Color.greyple()
        )
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