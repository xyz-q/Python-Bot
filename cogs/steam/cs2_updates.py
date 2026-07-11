import discord
from discord.ext import commands, tasks
import aiohttp
import feedparser
from datetime import datetime
import json
import os
import re

class CS2Updates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs2_app_id = "730"  # CS2's Steam app ID
        self.steam_news_url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={self.cs2_app_id}&count=5&maxlength=8000&format=json"
        self.notifications_file = ".json/cs2_notifications.json"
        self.last_update_file = ".json/cs2_last_update.json"
        self.max_seen_gids = 20
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
                data = json.load(f)
                # migrate old single-gid format
                if 'gid' in data and 'seen_gids' not in data:
                    data['seen_gids'] = [data['gid']] if data['gid'] else []
                if 'seen_gids' not in data:
                    data['seen_gids'] = []
                return data
        return {'seen_gids': []}
    
    def save_last_update(self, data):
        os.makedirs(os.path.dirname(self.last_update_file), exist_ok=True)
        with open(self.last_update_file, 'w') as f:
            json.dump(data, f)
    
    def mark_gid_seen(self, gid):
        data = self.load_last_update()
        seen = data.get('seen_gids', [])
        if gid not in seen:
            seen.append(gid)
        seen = seen[-self.max_seen_gids:]
        self.save_last_update({'seen_gids': seen, 'gid': gid})
    
    def clean_contents(self, raw_contents: str) -> str:
        """Convert Steam's HTML/BBCode line breaks into newlines, then strip remaining tags"""
        text = raw_contents
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<li[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'\[\*\]', '\n', text)
        text = re.sub(r'\[/?list[^\]]*\]', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^<]+?>', '', text)
        return text

    def format_changelog(self, raw_text: str) -> str:
        """Format raw changelog text into readable sections"""
        text = raw_text.replace('&quot;', '"').replace('&#39;', "'").replace('&amp;', '&').replace('\\', '')
        
        # Some posts use <br>/list markup (already split into lines by clean_contents).
        # Others are plain run-on sentences with no separators at all - periods
        # sometimes with no space before the next capitalized sentence. Split on
        # both to cover each style.
        lines = text.split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            sentences = re.split(r'\.\s*(?=[A-Z])', line)
            for sentence in sentences:
                sentence = sentence.strip().rstrip('.').strip()
                if sentence and len(sentence) > 3:
                    items.append(sentence)
        
        formatted = "**Counter-Strike 2 Update**\n\n**[ GAMEPLAY ]**\n\n"
        
        for item in items:
            formatted += f"• {item}\n\n"
        
        return formatted.strip()

    def pick_patch_item(self, newsitems):
        """Pick the newest item whose title matches patch keywords"""
        patch_keywords = ['update', 'patch', 'release', 'notes', 'changelog']
        candidates = [
            item for item in newsitems
            if any(k in item.get('title', '').lower() for k in patch_keywords)
        ]
        if not candidates:
            return newsitems[0] if newsitems else None
        return max(candidates, key=lambda i: i.get('date', 0))

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

            patch_item = self.pick_patch_item(data['appnews']['newsitems'])
            
            if not patch_item:
                await ctx.send("❌ No CS2 updates found.")
                return

            title = patch_item.get('title', 'No Title')
            contents = patch_item.get('contents', 'No content available')
            date = datetime.fromtimestamp(patch_item.get('date', 0))
            url = patch_item.get('url', '')
            
            # Clean up content
            clean_content = self.clean_contents(contents)
            formatted_content = self.format_changelog(clean_content)
            
            if len(formatted_content) > 4000:
                formatted_content = formatted_content[:4000] + "..."

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
    
    @commands.command()
    @commands.is_owner()
    async def testcs2dm(self, ctx):
        """Test CS2 update DM notification"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.steam_news_url) as response:
                    data = await response.json()
            
            patch_item = self.pick_patch_item(data['appnews']['newsitems'])
            await self.send_notifications(patch_item)
            await ctx.send("✅ Test notification sent to all subscribed users!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command()
    @commands.is_owner()
    async def cs2status(self, ctx):
        """Check CS2 update tracking status"""
        last_update = self.load_last_update()
        notifications = self.load_notifications()
        
        embed = discord.Embed(title="CS2 Update Status", color=0xF7931E)
        embed.add_field(name="Last Update ID", value=last_update.get('gid', 'None'), inline=False)
        embed.add_field(name="Seen GIDs", value=len(last_update.get('seen_gids', [])), inline=False)
        embed.add_field(name="Subscribers", value=len(notifications), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.is_owner()
    async def cs2clear(self, ctx):
        """Clear last update tracking to reset"""
        if os.path.exists(self.last_update_file):
            os.remove(self.last_update_file)
        await ctx.send("✅ CS2 update tracking cleared. Next check will treat current update as new.")
    
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
            
            patch_item = self.pick_patch_item(data['appnews']['newsitems'])
            if not patch_item:
                return
            
            current_update_id = patch_item.get('gid', '')
            last_update = self.load_last_update()
            
            if current_update_id and current_update_id not in last_update.get('seen_gids', []):
                # Save immediately to prevent duplicate sends
                self.mark_gid_seen(current_update_id)
                
                update_time = datetime.fromtimestamp(patch_item.get('date', 0))
                time_diff = datetime.now() - update_time
                
                if time_diff.total_seconds() < 86400:  # 24 hours
                    await self.send_notifications(patch_item)
                
        except Exception as e:
            print(f"Error checking CS2 updates: {e}")
            # Skip this check if network is down - will retry next cycle
            return
    
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
        
        clean_content = self.clean_contents(contents)
        formatted_content = self.format_changelog(clean_content)
        
        if len(formatted_content) > 4000:
            formatted_content = formatted_content[:4000] + "..."
        
        embed = discord.Embed(
            title=f"🚨 New CS2 Update: {title}",
            description=formatted_content,
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
                continue

async def setup(bot):
    await bot.add_cog(CS2Updates(bot))