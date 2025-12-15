import discord
from discord.ext import commands, tasks
import re
import ast
import aiohttp
from bs4 import BeautifulSoup
import json
import os
import datetime

def load_ely_data():
    with open(os.path.join(os.path.dirname(__file__), 'elydata.json'), 'r') as f:
        return json.load(f)

def save_ely_data(data):
    with open(os.path.join(os.path.dirname(__file__), 'elydata.json'), 'w') as f:
        json.dump(data, f, indent=2)

class UpdateView(discord.ui.View):
    def __init__(self, new_items):
        super().__init__(timeout=300)
        self.new_items = new_items
    
    @discord.ui.button(label='Merge Data', style=discord.ButtonStyle.green, emoji='✅')
    async def merge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            # Replace elysian spirit shield images in new items
            custom_ely_url = 'https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png?ex=68a50d6d&is=68a3bbed&hm=befb1351fcc88f72f0ab50e2204f92b516a56c6be0d7ca4869e3c780e11c32c9&'
            for item in self.new_items:
                if item['icon'] == '/show-image/elysian-spirit-shield.png':
                    item['icon'] = custom_ely_url
            
            # Load current data and merge
            current_data = load_ely_data()
            current_data.extend(self.new_items)
            
            # Save updated data
            save_ely_data(current_data)
            
            # Reload the ely cog to refresh data
            try:
                await interaction.client.reload_extension('cogs.Cmds.ely.ely')
                reload_msg = "\n\n✅ Data file reloaded successfully!"
            except:
                reload_msg = "\n\n⚠️ Could not reload data file automatically."
            
            embed = discord.Embed(
                title="✅ Data Updated Successfully!",
                description=f"Added **{len(self.new_items)}** new items to elydata.json{reload_msg}",
                color=0x00ff00
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Update Failed",
                description=f"Error: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red, emoji='❌')
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Update Cancelled",
            description="No changes were made to your data.",
            color=0xff0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class UpdateEly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_update.start()
    
    async def check_for_updates(self, html_content, current_data):
        """Extract new items from HTML script[4] and compare with existing data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            scripts = soup.find_all('script')
            
            if len(scripts) < 4:
                return None, "Not enough script tags found"
            
            script_content = scripts[3].string
            if not script_content:
                return None, "Script[3] is empty"
            
            pattern = r'data = (\[.*?\]);'
            match = re.search(pattern, script_content, re.DOTALL)
            
            if not match:
                return None, "No data array found in script[3]"
            
            new_data = ast.literal_eval(match.group(1))
            existing_ids = {item['id'] for item in current_data}
            new_items = [item for item in new_data if item['id'] not in existing_ids]
            return new_items, None
            
        except Exception as e:
            return None, f"Error parsing HTML: {str(e)}"
    
    def create_update_embed(self, new_items):
        """Create Discord embed showing new items"""
        if not new_items:
            embed = discord.Embed(
                title="📊 Ely Data Update Check",
                description="No new items found!",
                color=0x00ff00
            )
            return embed
        
        embed = discord.Embed(
            title="📊 New Items Found!",
            description=f"Found **{len(new_items)}** new items to add:",
            color=0xff9900
        )
        
        items_text = ""
        for i, item in enumerate(new_items[:10]):
            items_text += f"**{item['id']}** - {item['value']}\n"
        
        if len(new_items) > 10:
            items_text += f"\n... and **{len(new_items) - 10}** more items"
        
        embed.add_field(name="New Items", value=items_text, inline=False)
        embed.set_footer(text="Click buttons below to merge or cancel")
        
        return embed
    

    

    @commands.is_owner()
    @commands.command(name='updateely')
    async def update_ely_command(self, ctx, url: str = None):
        """Check for new items from ely.gg and offer to merge them"""
        
        if not url:
            url = "https://www.ely.gg"
        
        embed = discord.Embed(
            title="🔄 Checking for Updates...",
            description="Fetching latest data from ely.gg",
            color=0xffff00
        )
        message = await ctx.send(embed=embed)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html_content = await response.text()
            
            current_data = load_ely_data()
            new_items, error = await self.check_for_updates(html_content, current_data)
            
            if error:
                embed = discord.Embed(
                    title="❌ Error",
                    description=error,
                    color=0xff0000
                )
                await message.edit(embed=embed)
                return
            
            embed = self.create_update_embed(new_items)
            
            if new_items:
                view = UpdateView(new_items)
                await message.edit(embed=embed, view=view)
            else:
                await message.edit(embed=embed)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to fetch data: {str(e)}",
                color=0xff0000
            )
            await message.edit(embed=embed)
    
    async def auto_merge_updates(self, new_items):
        """Automatically merge new items without user interaction"""
        try:
            # Replace elysian spirit shield images
            custom_ely_url = 'https://cdn.discordapp.com/attachments/1241642636796887171/1319813845585494087/logo.png?ex=68a50d6d&is=68a3bbed&hm=befb1351fcc88f72f0ab50e2204f92b516a56c6be0d7ca4869e3c780e11c32c9&'
            for item in new_items:
                if item['icon'] == '/show-image/elysian-spirit-shield.png':
                    item['icon'] = custom_ely_url
            
            # Load current data and merge
            current_data = load_ely_data()
            current_data.extend(new_items)
            save_ely_data(current_data)
            
            # Reload the ely cog
            try:
                await self.bot.reload_extension('cogs.Cmds.ely.ely')
            except:
                pass
                
            return True
        except:
            return False
    
    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc))
    async def daily_update(self):
        """Daily automatic update check at 00:00 UTC"""
        try:
            channel = self.bot.get_channel(1449964057926041700)
            if not channel:
                return
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.ely.gg") as response:
                    html_content = await response.text()
            
            current_data = load_ely_data()
            new_items, error = await self.check_for_updates(html_content, current_data)
            
            if error or not new_items:
                embed = discord.Embed(
                    title="📊 Daily Ely Update",
                    description="No new items found today.",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
                return
            
            # Auto-merge the updates
            success = await self.auto_merge_updates(new_items)
            
            if success:
                embed = discord.Embed(
                    title="✅ Daily Ely Update - Items Added!",
                    description=f"Automatically added **{len(new_items)}** new items:",
                    color=0x00ff00
                )
                
                items_text = ""
                for item in new_items[:10]:
                    items_text += f"**{item['id']}** - {item['value']}\n"
                
                if len(new_items) > 10:
                    items_text += f"\n... and **{len(new_items) - 10}** more items"
                
                embed.add_field(name="New Items", value=items_text, inline=False)
            else:
                embed = discord.Embed(
                    title="❌ Daily Ely Update - Error",
                    description="Failed to merge new items automatically.",
                    color=0xff0000
                )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            try:
                channel = self.bot.get_channel(1449964057926041700)
                if channel:
                    embed = discord.Embed(
                        title="❌ Daily Ely Update - Error",
                        description=f"Update failed: {str(e)}",
                        color=0xff0000
                    )
                    await channel.send(embed=embed)
            except:
                pass
    
    @daily_update.before_loop
    async def before_daily_update(self):
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        self.daily_update.cancel()

async def setup(bot):
    await bot.add_cog(UpdateEly(bot))