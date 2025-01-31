import discord
from discord.ext import commands
import json
import os
import asyncio

class NotificationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notifications_file = '.json/notifications.json'
        self.load_or_create_data()
        # Add a dictionary to track message counts per user
        self.message_counters = {}
        # You can optionally add this to customize the interval
        self.message_interval = 7

    def load_or_create_data(self):
        if not os.path.exists(self.notifications_file):
            default_data = {
                "message": None,
                "readers": []
            }
            with open(self.notifications_file, 'w') as f:
                json.dump(default_data, f, indent=4)

    def get_data(self):
        with open(self.notifications_file, 'r') as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.notifications_file, 'w') as f:
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        
        if not ctx.valid or not ctx.command:
            return
            
        if ctx.command.name == "notification":
            return

        try:
            if not await ctx.command.can_run(ctx):
                return
        except commands.CommandError:
            return

        # Update message counter for this user
        user_id = str(message.author.id)
        
        # If this is the user's first message, initialize their counter to 1
        if user_id not in self.message_counters:
            self.message_counters[user_id] = 1
            should_notify = True  # Always notify on first command
        else:
            self.message_counters[user_id] += 1
            # After first message, only notify every 7th time
            should_notify = (self.message_counters[user_id] - 1) % self.message_interval == 0

        # Only proceed if it's the first message or every 7th after that
        if not should_notify:
            return

        # If we get here, it's either the first command or every 7th after
        data = self.get_data()
        if data["message"] and str(message.author.id) not in data["readers"]:
            embed = discord.Embed(
                title="Notification!",
                description="There's a new message out! Use `,notification`  and clear this message.",
                color=discord.Color.gold()
            )
            
            try:
                await asyncio.sleep(0.5)
                embed.set_footer(text="Please use ,report to send any bugs my way!")
                notif = await ctx.send(
                    embed=embed,
                    ephemeral=True
                )
                await asyncio.sleep(12)
                await notif.delete()
            except discord.HTTPException:
                pass



    @commands.command(name="notification", aliases=['notif'])
    async def notification(self, ctx):
        """View the current notification"""
        data = self.get_data()
        
        if not data["message"]:
            embed = discord.Embed(
                title="Notification",
                description="No notification available.",
                color=discord.Color.gold()
            )
        else:
            # Add user to readers list if they haven't read it yet
            if str(ctx.author.id) not in data["readers"]:
                data["readers"].append(str(ctx.author.id))
                self.save_data(data)

            embed = discord.Embed(
                title="A message from the developer.",
                description=data["message"],
                color=discord.Color.gold()
            )
            
            # Calculate reader number
            reader_number = len(data["readers"])
            embed.add_field(name=" ", value="Please use `,report` to send any bugs my way.", inline=False)
            embed.set_footer(text=f"You were #{reader_number} to read this alert!")

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="setnotification", aliases=['setnotif', 'notifset'])
    @commands.is_owner()
    async def set_notification(self, ctx, *, message):
        """Set a new notification (Admin only)"""
        new_data = {
            "message": message,
            "readers": []
        }
        self.save_data(new_data)
        
        embed = discord.Embed(
            title="✅ New Notification Set",
            description="Preview of the notification:",
            color=discord.Color.green()
        )
        embed.add_field(name="Content", value=message, inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="clearnotification", aliases=['clearnotif', 'notifclear'])
    @commands.is_owner()
    async def clear_notification(self, ctx):
        """Clear the current notification (Admin only)"""
        new_data = {
            "message": None,
            "readers": []
        }
        self.save_data(new_data)
        await ctx.send("✅ Notification cleared!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NotificationSystem(bot))
