



# Command : Send dms command
@bot.command()
@commands.has_permissions(administrator=True)  # Restrict this command to users with admin permissions
async def senddm(ctx, user_reference: str, *, message: str):
    user = None

    # Check if the user_reference is a mention
    mention_match = re.match(r'<@!?(\d+)>', user_reference)
    if mention_match:
        user_id = int(mention_match.group(1))
        user = await bot.fetch_user(user_id)
    else:
        # Try to find user by ID
        try:
            user_id = int(user_reference)
            user = await bot.fetch_user(user_id)
        except ValueError:
            # Try to find user by username
            user = discord.utils.get(ctx.guild.members, name=user_reference)

    if user:
        try:
            await user.send(message)
            await ctx.send(f"Successfully sent a DM to {user.name}.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to send a DM to this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to send DM: {e}")
    else:
        await ctx.send("User not found.")


# Command : View dms command
@bot.command()
@commands.has_permissions(administrator=True)
async def viewdms(ctx, user_reference: str):
    user = None

    # Check if the user_reference is a mention
    mention_match = re.match(r'<@!?(\d+)>', user_reference)
    if mention_match:
        user_id = int(mention_match.group(1))
        user = await bot.fetch_user(user_id)
    else:
        # Try to find user by ID
        try:
            user_id = int(user_reference)
            user = await bot.fetch_user(user_id)
        except ValueError:
            # Try to find user by username or display name
            user = discord.utils.get(ctx.guild.members, name=user_reference)
            if not user:
                user = discord.utils.get(ctx.guild.members, display_name=user_reference)

    if user:
        try:
            # Open DM channel with the user
            dm_channel = await user.create_dm()
            # Fetch the last 10 messages from the DM channel
            messages = []
            async for message in dm_channel.history(limit=10):
                messages.append(message)

            if messages:
                history = "\n".join(
                    [f"{message.created_at} - {message.author}: {message.content}" for message in messages])
                await ctx.send(f"DM history with {user.name}:\n{history}")
            else:
                await ctx.send(f"No recorded DMs with {user.name}.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to view DMs with this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to fetch DMs: {e}")
    else:
        await ctx.send("User not found.")


# Aiohttp

# Global variable for aiohttp session
session = None


# Command to force shutdown aiohttp session
@bot.command()
async def shutdown(ctx):
    global session
    if session:
        await session.close()
        session = None
        await ctx.send("aiohttp session closed.")
    else:
        await ctx.send("No active aiohttp session.")