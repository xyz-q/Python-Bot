# Handle command errors to prevent the bot from exiting unexpectedly
@bot.event
async def on_command_error(ctx, error):
    try:
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass  # If the message is not found, we pass since it might be already deleted.

    if isinstance(error, commands.CommandNotFound):
        bot_message = await ctx.send(f":warning: Command '{ctx.invoked_with}' not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        bot_message = await ctx.send("Missing required argument.")
    else:
        bot_message = await ctx.send("An error occurred.")
        print(f"An error occurred: {error}")

    await asyncio.sleep(7)
    await bot_message.delete()