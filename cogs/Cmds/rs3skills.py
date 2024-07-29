import discord
from discord.ext import tasks, commands
from runescape_player_api import RuneScapePlayerAPI

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.display_activities.start()

    def cog_unload(self):
        self.display_activities.cancel()

    @tasks.loop(minutes=10)
    async def display_activities(self):
        channel = self.bot.get_channel(1058255359753605150)
        player_name = "R0SA+PERCS"
        api = RuneScapePlayerAPI()
        player_data = api.get_player_data(player_name)

        if player_data:
            activities = player_data.get("activities", [])
            embed = discord.Embed(title="Activities", color=discord.Color.green())
            for activity in activities:
                name = activity.get("name", "Unknown Activity")
                description = activity.get("details", "No description available")
                embed.add_field(name=name, value=description, inline=False)

            await channel.send(embed=embed)
        else:
            print(f"Failed to fetch player data for {player_name}")

    @commands.command()
    async def show_activities(self, ctx, player_name: str):
        api = RuneScapePlayerAPI()
        player_data = api.get_player_data(player_name)

        if player_data:
            activities = player_data.get("activities", [])
            embed = discord.Embed(title="Activities", color=discord.Color.green())
            for activity in activities:
                description = activity.get("details", "No description available")
                embed.add_field(name=name, value=description, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Failed to fetch player data for {player_name}")

async def setup(bot):
    await bot.add_cog(Activities(bot))
