import discord
from discord.ext import commands
import json
import os
from discord.ui import Button, View
import asyncio



class WelcomeView(View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=90)
        self.cog = cog
        self.ctx = ctx
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        
        embed = self.message.embeds[0]
        embed.color = discord.Color.red()
        embed.set_footer(text="This menu has expired. Use ,welcome to start again.")
        
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Setup Channels", style=discord.ButtonStyle.blurple, emoji="⚙️")
    async def setup_channels(self, interaction: discord.Interaction, button: Button):
        modal = ChannelSetupModal(self.cog, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Welcome Message", style=discord.ButtonStyle.green, emoji="👋")
    async def welcome_message(self, interaction: discord.Interaction, button: Button):
        modal = WelcomeMessageModal(self.cog, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Leave Message", style=discord.ButtonStyle.red, emoji="👋")
    async def leave_message(self, interaction: discord.Interaction, button: Button):
        modal = LeaveMessageModal(self.cog, self)
        await interaction.response.send_modal(modal)

    async def update_view(self):
        """Update the welcome menu with current settings"""
        embed = discord.Embed(
            title="Welcome System Configuration",
            description="Use the buttons below to configure the welcome system:",
            color=discord.Color.gold()
        )
        
        guild_id = str(self.ctx.guild.id)
        if guild_id in self.cog.settings:
            welcome_channel = self.ctx.bot.get_channel(self.cog.settings[guild_id]["welcome_channel"])
            leave_channel = self.ctx.bot.get_channel(self.cog.settings[guild_id]["leave_channel"])
            
            settings_text = (
                f"**Welcome Channel:** {welcome_channel.mention if welcome_channel else 'Not set'}\n"
                f"**Leave Channel:** {leave_channel.mention if leave_channel else 'Not set'}\n"
                f"**Welcome Message:**\n```{self.cog.settings[guild_id]['join_message']}```\n"
                f"**Leave Message:**\n```{self.cog.settings[guild_id]['leave_message']}```"
            )
            
            embed.add_field(
                name="Current Settings",
                value=settings_text,
                inline=False
            )

        embed.add_field(
            name="Available Variables",
            value="{user} - Mentions the user (welcome) or shows username (leave)\n"
                  "{username} - Shows the username\n"
                  "{server} - Shows the server name",
            inline=False
        )
        
        embed.set_footer(text=f"This menu will timeout in {int(self.timeout)} seconds")
        
        await self.message.edit(embed=embed, view=self)

class ChannelSetupModal(discord.ui.Modal, title="Channel Setup"):
    def __init__(self, cog, view):
        super().__init__()
        self.cog = cog
        self.view = view

    welcome_channel = discord.ui.TextInput(
        label="Welcome Channel ID",
        placeholder="Enter the channel ID for welcome messages",
        required=True
    )
    
    leave_channel = discord.ui.TextInput(
        label="Leave Channel ID",
        placeholder="Enter the channel ID for leave messages",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            welcome_channel = await interaction.guild.fetch_channel(int(self.welcome_channel.value))
            leave_channel = await interaction.guild.fetch_channel(int(self.leave_channel.value))
            
            guild_id = str(interaction.guild.id)
            if guild_id not in self.cog.settings:
                self.cog.settings[guild_id] = {
                    "welcome_channel": welcome_channel.id,
                    "leave_channel": leave_channel.id,
                    "join_message": "Welcome, {user}! We hope you enjoy your stay.",
                    "leave_message": "Goodbye, {user}!\n\nWe'll miss you."
                }
            else:
                self.cog.settings[guild_id].update({
                    "welcome_channel": welcome_channel.id,
                    "leave_channel": leave_channel.id
                })
            
            self.cog.save_settings(self.cog.settings)
            
            embed = discord.Embed(
                title="✅ Channel Setup Complete",
                description=f"Welcome Channel: {welcome_channel.mention}\nLeave Channel: {leave_channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=8, delete_after=8)
            
            await self.view.update_view()
            
        except ValueError:
            await interaction.response.send_message("Please enter valid channel IDs!", ephemeral=True, delete_after=8, delete_after=8)
        except discord.NotFound:
            await interaction.response.send_message("One or both channels not found!", ephemeral=True, delete_after=8, delete_after=8)

class WelcomeMessageModal(discord.ui.Modal, title="Welcome Message Setup"):
    def __init__(self, cog, view):
        super().__init__()
        self.cog = cog
        self.view = view

    message = discord.ui.TextInput(
        label="Welcome Message",
        placeholder="Enter your welcome message. Use {user} for mention, {username} for name, {server} for server name",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.cog.settings:
            await interaction.response.send_message("Please setup channels first!", ephemeral=True, delete_after=8, delete_after=8)
            
            return
        
        self.cog.settings[guild_id]["join_message"] = self.message.value
        self.cog.save_settings(self.cog.settings)
        await self.view.update_view()

        formatted_message = self.message.value.format(
            user=interaction.user.mention,
            username=interaction.user.name,
            server=interaction.guild.name
        )
        
        preview_embed = discord.Embed(
            title=f"{interaction.user.display_name} pulled up.",
            description=formatted_message,
            color=discord.Color.gold()
        )
        if interaction.user.avatar:
            preview_embed.set_thumbnail(url=interaction.user.avatar.url)
        preview_embed.set_footer(text=f"Member #{len(interaction.guild.members)}")

        confirmation_embed = discord.Embed(
            title="✅ Welcome Message Updated",
            description="Your new welcome message has been saved. Here's how it will look:",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embeds=[confirmation_embed, preview_embed], ephemeral=True, delete_after=8, delete_after=8)

class LeaveMessageModal(discord.ui.Modal, title="Leave Message Setup"):
    def __init__(self, cog, view):
        super().__init__()
        self.cog = cog
        self.view = view

    message = discord.ui.TextInput(
        label="Leave Message",
        placeholder="Enter your leave message. Use {user} for name, {username} for name, {server} for server name",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.cog.settings:
            await interaction.response.send_message("Please setup channels first!", ephemeral=True, delete_after=8, delete_after=8)
            return
        
        self.cog.settings[guild_id]["leave_message"] = self.message.value
        self.cog.save_settings(self.cog.settings)
        await self.view.update_view()
        formatted_message = self.message.value.format(
            user=interaction.user.name,
            username=interaction.user.name,
            server=interaction.guild.name
        )
        
        preview_embed = discord.Embed(
            title=f"{interaction.user.display_name} has left.",
            description=formatted_message,
            color=discord.Color.red()
        )
        if interaction.user.avatar:
            preview_embed.set_thumbnail(url=interaction.user.avatar.url)
        preview_embed.set_footer(text=f"Members: {len(interaction.guild.members)}")

        confirmation_embed = discord.Embed(
            title="✅ Leave Message Updated",
            description="Your new leave message has been saved. Here's how it will look:",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embeds=[confirmation_embed, preview_embed], ephemeral=True, delete_after=8, delete_after=8)



class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = '.json/welcome_settings.json'
        self.settings = self.load_settings()

    def load_settings(self):
        """Load settings from JSON file, create if doesn't exist"""
        if not os.path.exists(self.settings_file):
            default_settings = {}
            self.save_settings(default_settings)
            return default_settings
        
        with open(self.settings_file, 'r') as f:
            return json.load(f)

    def save_settings(self, settings):
        """Save settings to JSON file"""
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)




    @commands.command(name="welcome")
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        """Welcome system configuration"""
        embed = discord.Embed(
            title="Welcome System Configuration",
            description="Use the buttons below to configure the welcome system:",
            color=discord.Color.gold()
        )
        
        guild_id = str(ctx.guild.id)
        if guild_id in self.settings:
            welcome_channel = self.bot.get_channel(self.settings[guild_id]["welcome_channel"])
            leave_channel = self.bot.get_channel(self.settings[guild_id]["leave_channel"])
            
            settings_text = (
                f"**Welcome Channel:** {welcome_channel.mention if welcome_channel else 'Not set'}\n"
                f"**Leave Channel:** {leave_channel.mention if leave_channel else 'Not set'}\n"
                f"**Welcome Message:**\n```{self.settings[guild_id]['join_message']}```\n"
                f"**Leave Message:**\n```{self.settings[guild_id]['leave_message']}```"
            )
            
            embed.add_field(
                name="Current Settings",
                value=settings_text,
                inline=False
            )

        embed.add_field(
            name="Available Variables",
            value="{user} - Mentions the user (welcome) or shows username (leave)\n"
                  "{username} - Shows the username\n"
                  "{server} - Shows the server name",
            inline=False
        )
        
        embed.set_footer(text="This menu will timeout in 90 seconds")
        
        view = WelcomeView(self, ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id not in self.settings:
            return

        channel_id = self.settings[guild_id]["welcome_channel"]
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            message = self.settings[guild_id]["join_message"]
            formatted_message = message.format(
                user=member.mention,
                username=member.name,
                server=member.guild.name
            )
            
            member_count = len(member.guild.members)
            
            embed = discord.Embed(
                title=f"{member.display_name} pulled up.",
                description=formatted_message,
                color=discord.Color.gold()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"Member #{member_count}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id not in self.settings:
            return

        channel_id = self.settings[guild_id]["leave_channel"]
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            message = self.settings[guild_id]["leave_message"]
            formatted_message = message.format(
                user=member.name,
                username=member.name,
                server=member.guild.name
            )
            
            embed = discord.Embed(
                title=f"{member.display_name} has left.",
                description=formatted_message,
                color=discord.Color.red()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
