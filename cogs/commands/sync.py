# Command : Command to sync bot tree
@bot.command()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Slash commands synchronized successfully!")
    await print("Slash commands synchronized successfully!")