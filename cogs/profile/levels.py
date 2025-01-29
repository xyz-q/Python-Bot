import json
import discord
from discord.ext import commands
import os
from cogs.Cmds.gamble import has_account


class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels_file = '.json/levels.json'
        self.gambling_stats_file = '.json/gambling_stats.json'
        self.special_levels_file = '.json/special_levels.json'
        self.load_levels()

    def load_levels(self):
        with open(self.levels_file, 'r') as f:
            self.levels_data = json.load(f)
        print("Loaded levels data:")
        print(json.dumps(self.levels_data, indent=2))

    async def get_user_data(self, user_id: str):
        """Get all level data for a user - can be called from other cogs"""
        try:
            with open(self.gambling_stats_file, 'r') as f:
                stats = json.load(f)
                total_wagered = stats.get(str(user_id), {}).get('total_wagered', 0)
        except FileNotFoundError:
            total_wagered = 0

        level_number, level_data = await self.get_user_level(str(user_id), total_wagered)
        
        # Calculate progress data
        progress_data = None
        if int(level_number) >= 0:
            next_level = str(int(level_number) + 1)
            if next_level in self.levels_data["levels"]:
                next_level_data = self.levels_data["levels"][next_level]
                required_more = next_level_data["required_wagered"] - total_wagered
                progress = (total_wagered / next_level_data["required_wagered"]) * 100
                progress_data = {
                    "next_level_name": next_level_data['name'],
                    "next_level_icon": next_level_data['icon'],
                    "progress_percent": progress,
                    "required_more": required_more
                }

        return {
            "level_number": level_number,
            "level_name": level_data['name'],
            "level_icon": level_data['icon'],
            "total_wagered": total_wagered,
            "progress_data": progress_data
        }

    async def get_user_level(self, user_id: str, total_wagered=0):
        # First check for special levels
        try:
            with open(self.special_levels_file, 'r') as f:
                special_levels = json.load(f)
                if str(user_id) in special_levels:
                    special_level = str(special_levels[str(user_id)])
                    return special_level, self.levels_data['levels'][special_level]
        except FileNotFoundError:
            pass
        
        # Regular level calculation
        current_level = "0"  # Start with default level
        for level, data in self.levels_data["levels"].items():
            if int(level) >= 0:  # Only check positive level numbers
                if total_wagered >= data["required_wagered"]:
                    current_level = level
                else:
                    break
        return current_level, self.levels_data["levels"][current_level]

    def get_level_info(self, level):
        level_str = str(level)
        level_data = self.levels_data["levels"][level_str]
        return {
            "icon": level_data["icon"],
            "name": level_data["name"],
            "required_wagered": level_data["required_wagered"]
        }

    def format_number(self, number: int) -> str:
        """Format number to K/M/B format"""
        if number >= 10_000_000_000:  # 10 Billion and above
            return f"{number/1_000_000_000:.2f}B"
        elif number >= 1_000_000:    # Millions (including 1-9.9B)
            return f"{int(number/1_000_000)}M"
        elif number >= 1_000:        # Thousands
            return f"{number/1_000:.1f}K"
        return str(number)



    def create_progress_bar(self, percent, length=10):
        """Create a progress bar - can be called from other cogs"""
        filled = int((percent/100) * length)
        return '█' * filled + '░' * (length - filled)
    
    @has_account()
    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        """Show level for yourself or another user"""
        # If no member is specified, use the command author
        target_user = member or ctx.author
        user_id = str(target_user.id)
        
        try:
            with open(self.gambling_stats_file, 'r') as f:
                stats = json.load(f)
                total_wagered = stats.get(user_id, {}).get('total_wagered', 0)
        except FileNotFoundError:
            total_wagered = 0

        level_number, level_data = await self.get_user_level(user_id, total_wagered)
        
        embed = discord.Embed(
            title=f"{target_user.name}'s Gambling Level", 
            color=discord.Color.gold()
        )
        
        # Set the user's avatar as the thumbnail
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Display level info
        level_display = f"{level_data['icon']} Level - {level_data['name']}"
        embed.add_field(name="Current Level", value=level_display, inline=False)
        embed.add_field(name="Total Wagered", value=self.format_number(total_wagered), inline=False)

        # Only show progress for regular levels
        if int(level_number) >= 0:
            next_level = str(int(level_number) + 1)
            if next_level in self.levels_data["levels"]:
                next_level_data = self.levels_data["levels"][next_level]
                required_more = next_level_data["required_wagered"] - total_wagered
                progress = (total_wagered / next_level_data["required_wagered"]) * 100
                progress_bar = self.create_progress_bar(progress)
                
                embed.add_field(
                    name=f"Progress to {next_level_data['name']} {next_level_data['icon']}", 
                    value=f"{progress_bar} {progress:.1f}%\nNeed: {self.format_number(required_more)} more", 
                    inline=False
                )

        await ctx.send(embed=embed)

    @has_account()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addlevel(self, ctx, level: int, required_wagered: int, icon: str, *, name: str):
        """Add or modify a level (Admin only)"""
        self.levels_data["levels"][str(level)] = {
            "required_wagered": required_wagered,
            "icon": icon,
            "name": name
        }
        with open(self.levels_file, 'w') as f:
            json.dump(self.levels_data, f, indent=4)
        await ctx.send(f"Level {level} ({name}) has been added/modified successfully!")

    @has_account()
    @commands.command()
    async def levels(self, ctx):
        embed = discord.Embed(title="Gambling Levels", color=discord.Color.gold())
        
        # First show special levels
        special_levels = {k: v for k, v in self.levels_data["levels"].items() if int(k) < 0}
        if special_levels:
            special_text = ""
            for level, data in special_levels.items():
                special_text += f"{data['icon']} Level {level} - {data['name']}\n"
            embed.add_field(name="Special Levels", value=special_text, inline=False)

        # Then show regular levels
        for level, data in self.levels_data["levels"].items():
            if int(level) >= 0:
                required = data["required_wagered"]
                formatted_required = self.format_number(required)
                embed.add_field(
                    name=f"Level {level} - {data['name']} {data['icon']}", 
                    value=f"Required Wagered: ${formatted_required}", 
                    inline=False
                )

        await ctx.send(embed=embed)

    @has_account()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addspeciallevel(self, ctx, level_number: int, icon: str, *, name: str):
        """Add a special level (Admin only)"""
        if level_number >= 0:
            await ctx.send("Special levels must use negative numbers (-1, -2, etc)")
            return
            
        self.levels_data["levels"][str(level_number)] = {
            "required_wagered": 0,
            "icon": icon,
            "name": name
        }
        with open(self.levels_file, 'w') as f:
            json.dump(self.levels_data, f, indent=4)
        await ctx.send(f"Special level {name} added successfully!")

    @has_account()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def assignspecial(self, ctx, user: discord.Member, level_number: int):
        """Assign a special level to a user (Admin only)"""
        if level_number >= 0:
            await ctx.send("Special levels must use negative numbers (-1, -2, etc)")
            return
            
        try:
            with open(self.special_levels_file, 'r') as f:
                special_levels = json.load(f)
        except FileNotFoundError:
            special_levels = {}

        special_levels[str(user.id)] = level_number
        
        with open(self.special_levels_file, 'w') as f:
            json.dump(special_levels, f, indent=4)
            
        await ctx.send(f"Assigned special level {level_number} to {user.name}")

    @has_account()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removespecial(self, ctx, user: discord.Member):
        """Remove special level from a user (Admin only)"""
        try:
            with open(self.special_levels_file, 'r+') as f:
                special_levels = json.load(f)
                if str(user.id) in special_levels:
                    del special_levels[str(user.id)]
                    f.seek(0)
                    json.dump(special_levels, f, indent=4)
                    f.truncate()
                    await ctx.send(f"Removed special level from {user.name}")
                else:
                    await ctx.send(f"{user.name} doesn't have a special level assigned")
        except FileNotFoundError:
            await ctx.send("No special levels have been assigned yet")

    @has_account()
    @commands.command()
    async def showspecials(self, ctx):
        """Show all special levels"""
        embed = discord.Embed(title="Special Levels", color=discord.Color.gold())
        
        special_levels = {k: v for k, v in self.levels_data["levels"].items() if int(k) < 0}
        if not special_levels:
            await ctx.send("No special levels found!")
            return

        for level, data in special_levels.items():
            embed.add_field(
                name=f"Level {level}",
                value=f"{data['icon']} {data['name']}",
                inline=False
            )
        
        await ctx.send(embed=embed)


    @has_account()
    @commands.command()
    async def alllevels(self, ctx, page: int = 1):
        """Show all users and their current levels (with pagination)"""
        try:
            with open(self.gambling_stats_file, 'r') as f:
                stats = json.load(f)
            
            try:
                with open(self.special_levels_file, 'r') as f:
                    special_levels = json.load(f)
            except FileNotFoundError:
                special_levels = {}

            embed = discord.Embed(title="All Users' Levels", color=discord.Color.gold())
            
            # Get and sort all users
            all_users = []
            for user_id, user_stats in stats.items():
                try:
                    member = await ctx.guild.fetch_member(int(user_id))
                    if member:
                        total_wagered = user_stats.get('total_wagered', 0)
                        level_number, level_data = await self.get_user_level(user_id, total_wagered)
                        
                        all_users.append({
                            'name': member.name,
                            'level_number': int(level_number),
                            'level_name': level_data['name'],
                            'level_icon': level_data['icon'],
                            'total_wagered': total_wagered
                        })
                except discord.NotFound:
                    continue

            # Sort users
            all_users.sort(key=lambda x: (-x['level_number'], -x['total_wagered']))

            # Pagination
            users_per_page = 10
            total_pages = max(1, (len(all_users) + users_per_page - 1) // users_per_page)
            
            # Validate page number
            page = max(1, min(page, total_pages))
            
            start_idx = (page - 1) * users_per_page
            end_idx = min(start_idx + users_per_page, len(all_users))
            
            page_text = ""
            for i, user in enumerate(all_users[start_idx:end_idx], start=start_idx + 1):
                wagered_formatted = self.format_number(user['total_wagered'])
                page_text += f"**{i}. {user['name']}**\n"
                page_text += f"{user['level_icon']} Level {user['level_number']} - {user['level_name']}\n"
                page_text += f"Total Wagered: ${wagered_formatted}\n\n"

            if not page_text:
                page_text = "No users found!"

            embed.description = page_text
            embed.set_footer(text=f"Page {page}/{total_pages} • Total Users: {len(all_users)}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")



async def setup(bot):
    await bot.add_cog(LevelSystem(bot))


# Example of how to access the LevelSystem cog from another cog:
# class AnotherCog(commands.Cog):
#     @commands.command()
#     async def somecommand(self, ctx):
#         level_cog = self.bot.get_cog('LevelSystem')
#         if level_cog:
#             user_data = await level_cog.get_user_data(ctx.author.id)
#             # Use the data however you need
#             level = user_data['level_number']
#             total_wagered = user_data['total_wagered']
#             # etc...
