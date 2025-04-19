import discord
from discord.ext import commands
from discord.ui import Button, View
import typing

class ServerButton(Button):
    def __init__(self, server: discord.Guild):
        super().__init__(label=f"{server.name}", style=discord.ButtonStyle.danger)
        self.server = server

    async def callback(self, interaction: discord.Interaction):
        confirm_view = ConfirmView(self.server, interaction.message)
        await interaction.response.send_message(
            f"Are you sure you want to remove the bot from {self.server.name}?",
            view=confirm_view,
            ephemeral=True
        )

class ConfirmView(View):
    def __init__(self, server: discord.Guild, original_message: discord.Message):
        super().__init__(timeout=60)
        self.server = server
        self.original_message = original_message

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        try:
            await self.server.leave()
            await interaction.response.edit_message(
                content=f"Successfully left {self.server.name}",
                view=None
            )
            # Delete the original server selection message
            await self.original_message.delete()
            # Delete the confirmation message after 5 seconds
            await interaction.message.delete(delay=5)
        except Exception as e:
            await interaction.response.edit_message(
                content=f"Failed to leave {self.server.name}: {str(e)}",
                view=None
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            content="Operation cancelled.",
            view=None
        )
        # Delete the original server selection message
        await self.original_message.delete()
        # Delete the cancellation message after 5 seconds
        await interaction.message.delete(delay=5)

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaveserver")
    @commands.is_owner()  # This ensures only the bot owner can use this command
    async def leave_server(self, ctx: commands.Context):
        """Lists all servers the bot is in and allows the owner to remove the bot from selected servers"""
        
        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass  # If we can't delete the message, continue anyway
        
        # Create a view that will hold all server buttons
        view = View(timeout=180)  # 3 minute timeout
        
        # Add a button for each server
        for guild in self.bot.guilds:
            view.add_item(ServerButton(guild))
        
        # Send the message with server buttons
        await ctx.send(
            "Select a server to remove the bot from:",
            view=view,
            ephemeral=True  # Makes the message only visible to the command user
        )

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            try:
                await ctx.message.delete()
            except:
                pass
            error_msg = await ctx.send("You must be the bot owner to use this command.")
            await error_msg.delete(delay=5)

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
