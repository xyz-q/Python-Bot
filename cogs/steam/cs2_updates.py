import discord
from discord.ext import commands, tasks
import aiohttp
import feedparser
from datetime import datetime
import json
import os

class CS2Updates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs2_app_id = "730"  # CS2's Steam app ID
        self.steam_news_url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={self.cs2_app_id}&count=5&maxlength=300&format=json"
        self.notifications_file = ".json/cs2_notifications.json"
        self.last_update_file = ".json/cs2_last_update.json"
        self.check_updates.start()
    
    def cog_unload(self):
        self.check_updates.cancel()
    
    def load_notifications(self):
        if os.path.exists(self.notifications_file):
            with open(self.notifications_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_notifications(self, data):
        os.makedirs(os.path.dirname(self.notifications_file), exist_ok=True)
        with open(self.notifications_file, 'w') as f:
            json.dump(data, f)
    
    def load_last_update(self):
        if os.path.exists(self.last_update_file):
            with open(self.last_update_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_last_update(self, data):
        os.makedirs(os.path.dirname(self.last_update_file), exist_ok=True)
        with open(self.last_update_file, 'w') as f:
            json.dump(data, f)
    
    def format_changelog(self, raw_text: str) -> str:
        """Format raw changelog text into readable sections"""
        import re
        # Clean HTML entities
        text = raw_text.replace('&quot;', '"').replace('&#39;', "'").replace('\\', '')
        
        # Split by periods and clean
        items = [item.strip() for item in text.split('.') if item.strip() and len(item.strip()) > 5]
        
        formatted = "**Counter-Strike 2 Update**\n\n**[ GAMEPLAY ]**\n\n"
        
        for item in items:
            if item:
                formatted += f"• {item}\n\n"
        
        return formatted.strip()

    @commands.command(aliases=['cs2patch', 'cs2update'])
    async def cs2updates(self, ctx):
        """Get the latest CS2 patch notes from Steam"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.steam_news_url) as response:
                    if response.status != 200:
                        await ctx.send("❌ Failed to fetch CS2 updates from Steam.")
                        return
                    
                    data = await response.json()
                    
            if not data.get('appnews', {}).get('newsitems'):
                await ctx.send("❌ No CS2 updates found.")
                return

            # Filter for patch notes/updates (not just any news)
            patch_keywords = ['update', 'patch', 'release', 'notes', 'changelog']
            patch_item = None
            
            for item in data['appnews']['newsitems']:
                title = item.get('title', '').lower()
                if any(keyword in title for keyword in patch_keywords):
                    patch_item = item
                    break
            
            if not patch_item:
                patch_item = data['appnews']['newsitems'][0]  # Fallback to latest

            title = patch_item.get('title', 'No Title')
            contents = patch_item.get('contents', 'No content available')
            date = datetime.fromtimestamp(patch_item.get('date', 0))
            url = patch_item.get('url', '')
            
            # Clean up content
            import re
            clean_content = re.sub('<[^<]+?>', '', contents)
            formatted_content = self.format_changelog(clean_content)
            
            if len(formatted_content) > 2000:
                formatted_content = formatted_content[:2000] + "..."

            embed = discord.Embed(
                title=f"🔧 {title}",
                description=formatted_content,
                color=0xF7931E,
                url=url
            )
            
            embed.add_field(
                name="📅 Release Date",
                value=date.strftime('%B %d, %Y at %H:%M UTC'),
                inline=True
            )
            
            embed.set_footer(text="Latest CS2 Patch Notes from Steam", icon_url="https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching CS2 updates: {str(e)}")
    
    @commands.command()
    async def cs2notify(self, ctx):
        """Toggle CS2 update notifications in DMs"""
        notifications = self.load_notifications()
        user_id = str(ctx.author.id)
        
        if user_id in notifications:
            del notifications[user_id]
            self.save_notifications(notifications)
            await ctx.send("🔕 CS2 update notifications disabled.")
        else:
            notifications[user_id] = True
            self.save_notifications(notifications)
            await ctx.send("🔔 CS2 update notifications enabled! You'll receive DMs when new updates drop.")
    
    @tasks.loop(minutes=30)
    async def check_updates(self):
        """Check for new CS2 updates every 30 minutes"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.steam_news_url) as response:
                    if response.status != 200:
                        return
                    data = await response.json()
            
            if not data.get('appnews', {}).get('newsitems'):
                return
            
            # Get latest patch
            patch_keywords = ['update', 'patch', 'release', 'notes', 'changelog']
            patch_item = None
            
            for item in data['appnews']['newsitems']:
                title = item.get('title', '').lower()
                if any(keyword in title for keyword in patch_keywords):
                    patch_item = item
                    break
            
            if not patch_item:
                patch_item = data['appnews']['newsitems'][0]
            
            # Check if this is a new update
            last_update = self.load_last_update()
            current_update_id = patch_item.get('gid', '')
            
            if last_update.get('gid') != current_update_id:
                # New update found, send notifications
                await self.send_notifications(patch_item)
                self.save_last_update({'gid': current_update_id})
                
        except Exception as e:
            print(f"Error checking CS2 updates: {e}")
    
    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()
    
    async def send_notifications(self, patch_item):
        """Send DM notifications to subscribed users"""
        notifications = self.load_notifications()
        
        title = patch_item.get('title', 'No Title')
        contents = patch_item.get('contents', 'No content available')
        date = datetime.fromtimestamp(patch_item.get('date', 0))
        url = patch_item.get('url', '')
        
        import re
        clean_content = re.sub('<[^<]+?>', '', contents)
        if len(clean_content) > 400:
            clean_content = clean_content[:400] + "..."
        
        embed = discord.Embed(
            title=f"🚨 New CS2 Update: {title}",
            description=clean_content,
            color=0xF7931E,
            url=url
        )
        embed.add_field(
            name="📅 Release Date",
            value=date.strftime('%B %d, %Y at %H:%M UTC'),
            inline=True
        )
        embed.set_footer(text="CS2 Update Notification")
        
        for user_id in notifications:
            try:
                user = self.bot.get_user(int(user_id))
                if user:
                    await user.send(embed=embed)
            except Exception as e:
                print(f"Failed to send notification to {user_id}: {e}")

async def setup(bot):
    await bot.add_cog(CS2Updates(bot))