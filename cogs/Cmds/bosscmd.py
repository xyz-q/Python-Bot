import discord
from discord.ext import commands
import random
import json
import os

SAVE_FILE = "boss_drops.json"

class BossDrops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def add_drops(self, ctx):
        """Interactive command to add boss drops."""
        drops = {}
        await ctx.send("Enter the boss drops and their drop rates (e.g., 'Pet 1/200'). Type 'done' when finished.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        while True:
            try:
                user_input = await self.bot.wait_for("message", check=check, timeout=120)
                if user_input.content.lower() == 'done':
                    await ctx.send("Drops entry completed.")
                    break

                drop_name, rate = user_input.content.split()
                numerator, denominator = map(int, rate.split('/'))
                if numerator != 1 or denominator <= 0:
                    raise ValueError

                drops[drop_name] = numerator / denominator
            except ValueError:
                await ctx.send("Invalid input. Format must be 'DropName 1/Rate'. Rate must be positive.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")

        if drops:
            await ctx.send("Enter the boss name for these drops:")
            boss_name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            boss_name = boss_name_msg.content.strip()

            if boss_name:
                await ctx.send(f"Do you want to save the drops for boss '{boss_name}'? (yes/no)")
                save_option = await self.bot.wait_for("message", check=check, timeout=60)

                if save_option.content.lower() == 'yes':
                    self.save_drops(boss_name, drops)
                    await ctx.send(f"Drops for boss '{boss_name}' saved successfully!")
                else:
                    await ctx.send("Drops not saved.")

    @commands.command()
    async def simulate(self, ctx, boss_name: str, kill_count: int):
        """Simulate kills for a given boss."""
        print(f"Simulate command invoked: boss_name={boss_name}, kill_count={kill_count}")

        if kill_count <= 0:
            await ctx.send("Kill count must be a positive integer.")
            return

        boss_drops = self.load_drops_for_boss(boss_name)
        print(f"Loaded boss drops: {boss_drops}")

        if not boss_drops:
            await ctx.send(f"No saved drops found for boss '{boss_name}'.")
            return

        results = self.simulate_kills(boss_drops, kill_count)
        print(f"Simulation results: {results}")

        if not results:
            await ctx.send("Simulation failed to generate results.")
            return

        results_message = f"**Simulation Results for {kill_count} kills:**\n"

        for drop, count in results.items():
            percentage = (count / kill_count) * 100
            results_message += f"{drop}: {count} drops ({percentage:.2f}%)\n"

        await ctx.send(results_message)

    def save_drops(self, boss_name, drops):
        """Saves the drops for a boss."""
        data = {}
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as file:
                data = json.load(file)

        data[boss_name] = drops
        with open(SAVE_FILE, 'w') as file:
            json.dump(data, file, indent=4)

    def load_drops_for_boss(self, boss_name):
        """Loads saved drops for a specific boss."""
        if not os.path.exists(SAVE_FILE):
            return {}

        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)

        return data.get(boss_name, {})

    def simulate_kills(self, drops, kill_count):
        """Simulates boss kills and records drops."""
        results = {drop: 0 for drop in drops}
        for _ in range(kill_count):
            for drop, rate in drops.items():
                if random.random() < rate:
                    results[drop] += 1
        return results

async def setup(bot):
    await bot.add_cog(BossDrops(bot))
