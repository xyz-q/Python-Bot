import discord
from discord.ext import commands
import re
import ast
import aiohttp
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from cogs.Cmds.ely.elydata import data as current_data

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
            
            # Merge data
            current_data.extend(self.new_items)
            
            # Update file
            file_path = os.path.join(os.path.dirname(__file__), 'elydata.py')
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_data_str = str(current_data)
            pattern = r'data = \[.*?\]'
            new_content = re.sub(pattern, f'data = {new_data_str}', content, flags=re.DOTALL)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            embed = discord.Embed(
                title="✅ Data Updated Successfully!",
                description=f"Added **{len(self.new_items)}** new items to elydata.py",
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
    
    async def check_for_updates(self, html_content):
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
    
    @commands.command(name='checkhtml')
    async def check_html_structure(self, ctx, url: str = None):
        """Check HTML structure and script tags from ely.gg"""
        
        if not url:
            url = "https://www.ely.gg"
        
        embed = discord.Embed(
            title="🔍 Checking HTML Structure...",
            description=f"Analyzing: {url}",
            color=0xffff00
        )
        message = await ctx.send(embed=embed)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            scripts = soup.find_all('script')
            
            embed = discord.Embed(
                title="📋 HTML Structure Analysis",
                color=0x00ff00
            )
            
            embed.add_field(
                name="Script Tags Found",
                value=f"Total: **{len(scripts)}** script tags",
                inline=False
            )
            
            # Check each script for data array
            found_data = []
            for i, script in enumerate(scripts):
                if script.string and 'data = [' in script.string:
                    found_data.append(f"Script[{i}] contains data array")
            
            if found_data:
                embed.add_field(
                    name="Data Arrays Found",
                    value="\n".join(found_data),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Data Arrays",
                    value="No 'data = [' arrays found in any script tags",
                    inline=False
                )
            
            # Show first few characters of each script
            script_preview = ""
            for i, script in enumerate(scripts[:8]):  # Show first 8 scripts
                content = script.string[:50] if script.string else "(empty or external)"
                script_preview += f"**[{i}]** {content}...\n"
            
            if len(scripts) > 8:
                script_preview += f"... and {len(scripts) - 8} more scripts"
            
            embed.add_field(
                name="Script Preview",
                value=script_preview or "No scripts found",
                inline=False
            )
            
            await message.edit(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to analyze HTML: {str(e)}",
                color=0xff0000
            )
            await message.edit(embed=embed)
    
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
            
            new_items, error = await self.check_for_updates(html_content)
            
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

async def setup(bot):
    await bot.add_cog(UpdateEly(bot))