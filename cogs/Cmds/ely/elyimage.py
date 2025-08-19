import discord
from discord.ext import commands
from difflib import get_close_matches
import json
import os

def load_ely_data():
    with open(os.path.join(os.path.dirname(__file__), 'elydata.json'), 'r') as f:
        return json.load(f)

def save_ely_data(data):
    with open(os.path.join(os.path.dirname(__file__), 'elydata.json'), 'w') as f:
        json.dump(data, f, indent=2)



class SetImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def search_items(self, query):
        data = load_ely_data()
        
        # Exact match first
        exact_matches = [item for item in data if query.lower() == item['value'].lower()]
        if exact_matches:
            return exact_matches
        
        # Contains match
        contains_matches = [item for item in data if query.lower() in item['value'].lower()]
        if contains_matches:
            return contains_matches
        
        # Fuzzy matching with higher cutoff
        item_names = [item['value'] for item in data]
        close_matches = get_close_matches(query, item_names, n=10, cutoff=0.6)
        
        return [item for item in data if item['value'] in close_matches]
    
    @commands.command(name='setimage')
    async def set_image(self, ctx, *, args: str):
        """Set/update an item's image. Usage: ,setimage "item name" "image_url" """
        
        # Split args to get item name and image URL
        parts = args.rsplit(' ', 1)
        if len(parts) != 2:
            await ctx.send("Usage: `,setimage item_name image_url`")
            return
        
        item_name, image_url = parts
        matches = self.search_items(item_name)
        
        if not matches:
            embed = discord.Embed(
                title="❌ No Items Found",
                description=f"No items found matching: **{item_name}**",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        if len(matches) == 1:
            # Single match - update directly
            item = matches[0]
            data = load_ely_data()
            
            for data_item in data:
                if data_item['id'] == item['id']:
                    old_icon = data_item['icon']
                    data_item['icon'] = image_url
                    break
            
            save_ely_data(data)
            
            # Reload ely cog
            try:
                await self.bot.reload_extension('cogs.Cmds.ely.ely')
                reload_msg = "\n\n✅ Ely cog reloaded!"
            except:
                reload_msg = "\n\n⚠️ Could not reload ely cog. Use `!reload ely`."
            
            embed = discord.Embed(
                title="✅ Image Updated!",
                description=f"**{item['value']}** (ID: {item['id']})\n\nOld: {old_icon}\nNew: {image_url}{reload_msg}",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        
        else:
            # Multiple matches - show list
            embed = discord.Embed(
                title="🔍 Multiple Items Found",
                description=f"Found **{len(matches)}** items matching: **{item_name}**\n\nPlease be more specific:",
                color=0xffff00
            )
            
            items_list = "\n".join([f"**{item['id']}** - {item['value']}" for item in matches[:10]])
            if len(matches) > 10:
                items_list += f"\n... and {len(matches) - 10} more"
            
            embed.add_field(name="Matching Items", value=items_list, inline=False)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SetImage(bot))