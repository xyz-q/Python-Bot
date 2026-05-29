import subprocess
import discord
from discord.ext import commands

class Deploy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deploy(self, ctx):
        if ctx.author.id != 110927272210354176:
            return await ctx.send("no permission")

        msg = await ctx.send("Deploying...")

        process = subprocess.run(
            ["bash", "/home/matty0/bot/Python-Bot/deploy.sh"],
            capture_output=True,
            text=True
        )

        output = process.stdout + "\n" + process.stderr

        # Parse useful info
        status = "UNKNOWN"
        before = None
        after = None
        changed = []

        for line in output.splitlines():
            if "STATUS=" in line:
                status = line.split("=",1)[1]
            if "BEFORE=" in line:
                before = line.split("=",1)[1]
            if "AFTER=" in line:
                after = line.split("=",1)[1]
            if "CHANGED_FILES=" in line:
                changed = line.replace("CHANGED_FILES=", "").split()

        color = discord.Color.green() if status == "SUCCESS" else discord.Color.red()

        embed = discord.Embed(
            title="🚀 Bot Deployment",
            description=f"Status: **{status}**",
            color=color
        )

        if before and after:
            embed.add_field(name="Commit", value=f"`{before[:7]} → {after[:7]}`", inline=False)

        if changed:
            embed.add_field(
                name="Changed Files",
                value="\n".join(changed[:10]) if changed else "None",
                inline=False
            )

        embed.set_footer(text="DL20 Deployment System")

        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Deploy(bot))