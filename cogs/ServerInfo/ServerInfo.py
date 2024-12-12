from discord.ext import commands
import discord

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.dm_only()  # This ensures the command only works in DMs
    @commands.command()
    async def serverlist(self, ctx):
        try:
            servers_list = []
            for guild in self.bot.guilds:
                servers_list.append(f"Server: {guild.name} (ID: {guild.id})")
            
            # Split into multiple messages if too long
            message = "\n".join(servers_list)
            if len(message) > 1900:  # Discord has 2000 char limit, leaving room for formatting
                chunks = [servers_list[i:i + 20] for i in range(0, len(servers_list), 20)]
                for chunk in chunks:
                    await ctx.send("\n".join(chunk))
            else:
                await ctx.send(message)
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
    
    @commands.dm_only()
    @commands.command()
    async def channellist(self, ctx, server_id: int):
        try:
            guild = self.bot.get_guild(server_id)
            if guild is None:
                await ctx.send("Server not found! Make sure you provided the correct server ID.")
                return
            
            channels_list = [f"Channels in {guild.name}:"]
            
            # Organize channels by category
            categories = {}
            no_category = []
            
            for channel in guild.channels:
                if isinstance(channel, discord.CategoryChannel):
                    categories[channel.id] = {
                        "name": channel.name,
                        "channels": []
                    }
            
            for channel in guild.channels:
                if not isinstance(channel, discord.CategoryChannel):
                    if channel.category_id:
                        categories[channel.category_id]["channels"].append(
                            f"  └─ {channel.name} (ID: {channel.id}) - {channel.type}"
                        )
                    else:
                        no_category.append(
                            f"  {channel.name} (ID: {channel.id}) - {channel.type}"
                        )
            
            # Add no-category channels first
            if no_category:
                channels_list.append("\nNo Category:")
                channels_list.extend(no_category)
            
            # Add categorized channels
            for category in categories.values():
                if category["channels"]:  # Only show categories that have channels
                    channels_list.append(f"\n{category['name']}:")
                    channels_list.extend(category["channels"])
            
            # Split into multiple messages if too long
            message = "\n".join(channels_list)
            if len(message) > 1900:
                chunks = [channels_list[i:i + 20] for i in range(0, len(channels_list), 20)]
                for chunk in chunks:
                    await ctx.send("\n".join(chunk))
            else:
                await ctx.send(message)
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @serverlist.error
    @channellist.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in DMs!")
        else:
            await ctx.send(f"An error occurred: {str(error)}")




async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
