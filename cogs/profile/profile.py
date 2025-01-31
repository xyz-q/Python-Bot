import discord
from discord.ext import commands
from typing import Dict, Any
from datetime import datetime
import os
import json

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vault_file = ".json/vaults.json"
        self.currency_file = ".json/currency.json"

    def get_net_worth(self, user_id: str) -> int:
        """Calculate user's total net worth from vault and currency"""
        total = 0
        
        # Get vault balance
        try:
            if os.path.exists(self.vault_file):
                with open(self.vault_file, 'r') as f:
                    vault_data = json.load(f)
                    # Check if user exists in vault data and get their balance
                    if str(user_id) in vault_data:
                        user_vault = vault_data[str(user_id)]
                        if isinstance(user_vault, dict) and 'balance' in user_vault:
                            total += user_vault['balance']
                        print(f"Vault data for {user_id}: {user_vault}")  # Debug print
        except Exception as e:
            print(f"Error reading vault.json: {e}")
            print(f"Vault data structure: {vault_data}")  # Debug print

        # Get currency balance
        try:
            if os.path.exists(self.currency_file):
                with open(self.currency_file, 'r') as f:
                    currency_data = json.load(f)
                    # Add currency balance if it exists
                    total += currency_data.get(str(user_id), 0)
                    print(f"Currency data for {user_id}: {currency_data.get(str(user_id), 0)}")  # Debug print
        except Exception as e:
            print(f"Error reading currency.json: {e}")

        return total


    def format_number(self, number: int) -> str:
        """Format number to K/M/B format"""
        if number >= 10_000_000_000:  # 10 Billion and above
            return f"{number/1_000_000_000:.2f}B"
        elif number >= 1_000_000:    # Millions (including 1-9.9B)
            return f"{int(number/1_000_000)}M"
        elif number >= 1_000:        # Thousands
            return f"{number/1_000:.1f}K"
        return str(number)


    async def get_first_seen_data(self, user_id: int) -> dict:
        """Get first-seen data for user"""
        first_seen_cog = self.bot.get_cog('FirstSeen')
        if not first_seen_cog:
            return None
        
        first_seen = first_seen_cog.get_first_seen(user_id)
        if not first_seen:
            return None

        return {
            'timestamp': first_seen,
        }

    async def get_gambling_data(self, user_id: int) -> Dict[str, Any]:
        """Get gambling-related profile data"""
        level_cog = self.bot.get_cog('LevelSystem')
        if not level_cog:
            return None
        
        data = await level_cog.get_user_data(user_id)
        if data:
            data['user_id'] = user_id  # Add user_id to the data
        return data

    async def get_command_stats(self, user_id: int) -> Dict[str, Any]:
        """Get command statistics data"""
        stats_cog = self.bot.get_cog('CommandStats')
        if not stats_cog:
            return None

        total_commands = stats_cog.get_total_commands(user_id)
        favorite_command, favorite_count = stats_cog.get_favorite_command(user_id) or (None, 0)

        return {
            'total': total_commands,
            'favorite': favorite_command,
            'favorite_count': favorite_count
        }

    def add_gambling_fields(self, embed: discord.Embed, gambling_data: Dict[str, Any]):
        """Add gambling-related fields to embed"""
        if not gambling_data:
            embed.add_field(name="Gambling Stats", value="Not available", inline=False)
            return

        # Add level information
        level_text = f"{gambling_data['level_icon']} `{gambling_data['level_name']}`"
        embed.add_field(name="Rank", value=level_text, inline=False)

        # Get net worth
        net_worth = self.get_net_worth(gambling_data.get('user_id', 0))
        
        # Create combined field for wagered and net worth
        stats_text = (
            f"<:goldpoints:1319902464115343473> Net Worth - `{self.format_number(net_worth)}` \n"
            f"<:gamba:1328512027282374718> Total Wagered - `{self.format_number(gambling_data['total_wagered'])}` "
        )
        embed.add_field(name="Staking Stats", value=stats_text, inline=False)

        # Add progress bar if available
        if gambling_data['progress_data']:
            level_cog = self.bot.get_cog('LevelSystem')
            progress = gambling_data['progress_data']
            progress_bar = level_cog.create_progress_bar(progress['progress_percent'])
            progress_text = (
                f"{progress_bar} {progress['next_level_icon']} \n"
                #f" You need {self.format_number(progress['required_total'])}"
                #f"{progress['next_level_name']} {progress['next_level_icon']}\n"
                #f"{gambling_data['level_icon']}        {progress['next_level_icon']}\n"
                
            )
            embed.add_field(name=f"Level Progress {progress['progress_percent']:.1f}%", value=progress_text, inline=False)

    def add_command_stats_fields(self, embed: discord.Embed, stats_data: Dict[str, Any]):
        """Add command statistics fields to embed"""
        if not stats_data:
            embed.add_field(
                name="Commands",
                value="Total - `0`\nFavorite - `None`",
                inline=True
            )
            return

        # Format the commands section
        commands_text = (
            f"Total - `{self.format_number(stats_data['total'])}`\n"  # Updated to use self.format_number
            f"Favorite - `{stats_data['favorite'] if stats_data['favorite'] else 'None'}`"
        )

        embed.add_field(
            name="Command Stats",
            value=commands_text,
            inline=True
        )


    def add_prestige_fields(self, embed: discord.Embed, first_seen_data: dict):
        """Add prestige information to embed"""
        if not first_seen_data:
            return

        timestamp = first_seen_data['timestamp']
        prestige_data = self.calculate_prestige(timestamp)
        
        if prestige_data['level'] > 0:
            prestige_text = (
                f"{prestige_data['icon']} __**{prestige_data['name']}**__\n"
                
            )
            embed.add_field(
                name=f"{prestige_text}",
                value=" ",
                inline=False
            )

    def calculate_prestige(self, first_seen_timestamp: datetime) -> dict:
        """Calculate prestige level based on years since first seen"""
        now = datetime.now()
        years_diff = (now - first_seen_timestamp).days / 365.25  # Using 365.25 to account for leap years
        
        prestige_level = int(years_diff)  # Full years only
        
        # Prestige icons/names based on years (you can customize these)
        prestige_icons = {
            0: " ",  # No prestige
            1: "<:prestige1:1334791356765175879>",  # 1 year
            2: "<:prestige2:1334791402068119572>",  # 2 years
            3: "<:prestige3:1334801979964129300>",  # 3 years
            4: "<:prestige4:1334791804087963720>",  # 4 years
            5: "<:prestige5:1334791823436025878>",  # 5+ years
        }
        
        prestige_names = {
            0: " ",
            1: "1 Year",
            2: "2 Years",
            3: "3 Years",
            4: "4 Years",
            5: "5 Years",
        }
        
        # Get icon and name (default to highest tier if years > 5)
        icon = prestige_icons.get(min(prestige_level, 5))
        name = prestige_names.get(min(prestige_level, 5))
        
        return {
            'level': prestige_level,
            'icon': icon,
            'name': name,
            'years': years_diff
        }


    @commands.command()
    async def profile(self, ctx, member: discord.Member = None):
        """Display user profile with various statistics"""
        target_user = member or ctx.author
        
        # Create the base embed
        embed = discord.Embed(
            title=f"{target_user.display_name.title()}'s Profile",
            color=target_user.color
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)

        # Add first seen date
        first_seen_data = await self.get_first_seen_data(target_user.id)
        self.add_prestige_fields(embed, first_seen_data)
        # Get and add gambling data (now includes net worth)
        gambling_data = await self.get_gambling_data(target_user.id)
        self.add_gambling_fields(embed, gambling_data)

        # Get and add command stats
        stats_data = await self.get_command_stats(target_user.id)
        self.add_command_stats_fields(embed, stats_data)

        #
        
        if first_seen_data:
            timestamp = first_seen_data['timestamp']
            embed.set_footer(text=f"First seen on {timestamp.strftime('%B %d, %Y')}")

            # Add prestige information
            
        else:
            embed.set_footer(text=f"No commands run.")

        # Add footer with user ID
        

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))

