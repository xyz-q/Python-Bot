import discord
from discord.ext import commands
import re
import ast
import aiohttp
from bs4 import BeautifulSoup
from elydata import data as current_data

async def check_for_updates(html_content):
    """Extract new items from HTML script[4] and compare with existing data"""
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        if len(scripts) < 5:  # script[4] means 5th script tag
            return None, "Not enough script tags found"
        
        script_content = scripts[4].string
        if not script_content:
            return None, "Script[4] is empty"
        
        # Extract data array from script
        pattern = r'data = (\[.*?\]);'
        match = re.search(pattern, script_content, re.DOTALL)
        
        if not match:
            return None, "No data array found in script[4]"
        
        new_data = ast.literal_eval(match.group(1))
        existing_ids = {item['id'] for item in current_data}
        new_items = [item for item in new_data if item['id'] not in existing_ids]
        return new_items, None
        
    except Exception as e:
        return None, f"Error parsing HTML: {str(e)}"

def create_update_embed(new_items):
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
    
    # Show first 10 items in embed
    items_text = ""
    for i, item in enumerate(new_items[:10]):
        items_text += f"**{item['id']}** - {item['value']}\n"
    
    if len(new_items) > 10:
        items_text += f"\n... and **{len(new_items) - 10}** more items"
    
    embed.add_field(name="New Items", value=items_text, inline=False)
    embed.set_footer(text="React with ✅ to merge or ❌ to cancel")
    
    return embed

async def merge_data(new_items):
    """Merge new items into existing data and update file"""
    current_data.extend(new_items)
    
    # Read current file
    with open('u:/DISCORD BOT/elydata.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace data array
    new_data_str = str(current_data).replace("'", "'")
    pattern = r'data = \[.*?\]'
    new_content = re.sub(pattern, f'data = {new_data_str}', content, flags=re.DOTALL)
    
    # Write back to file
    with open('u:/DISCORD BOT/elydata.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

class UpdateView(discord.ui.View):
    def __init__(self, new_items):
        super().__init__(timeout=300)
        self.new_items = new_items
        self.result = None
    
    @discord.ui.button(label='Merge Data', style=discord.ButtonStyle.green, emoji='✅')
    async def merge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            await merge_data(self.new_items)
            
            embed = discord.Embed(
                title="✅ Data Updated Successfully!",
                description=f"Added **{len(self.new_items)}** new items to elydata.py",
                color=0x00ff00
            )
            
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            self.result = "merged"
            
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
        self.result = "cancelled"

# Command to check for updates
@commands.command(name='update_ely')
async def update_ely_command(ctx, url: str = None):
    """Check for new items from ely.gg and offer to merge them"""
    
    if not url:
        url = "https://www.ely.gg"  # Default URL
    
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
        
        new_items, error = await check_for_updates(html_content)
        
        if error:
            embed = discord.Embed(
                title="❌ Error",
                description=error,
                color=0xff0000
            )
            await message.edit(embed=embed)
            return
        
        embed = create_update_embed(new_items)
        
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