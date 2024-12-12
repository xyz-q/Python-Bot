import discord
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

class RunescapePrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')

    @commands.command(name='price', aliases=['rscheck', 'pc'])
    async def check_price(self, ctx, *, item_name: str):
        """Check the price of a RuneScape 3 item"""
        # Start typing indicator at the very beginning
        async with ctx.typing():  # This will show typing until the with block ends
            try:
                formatted_item = item_name.replace(' ', '%20')
                url = f"https://www.ely.gg/search?search_item={formatted_item}"
                
                driver = webdriver.Chrome(options=self.chrome_options)
                try:
                    print(f"Navigating to URL: {url}")
                    driver.get(url)
                    time.sleep(2)
                    
                    elements = driver.find_elements(By.TAG_NAME, "a")
                    print(f"Found {len(elements)} clickable elements")
                    
                    item_element = None
                    for element in elements:
                        if item_name.lower() in element.text.lower():
                            item_element = element
                            print(f"Found matching element: {element.text}")
                            break
                    
                    if item_element:
                        print("Clicking item element")
                        driver.execute_script("arguments[0].click();", item_element)
                        time.sleep(3)
                        
                        price_element = driver.find_element(By.ID, "stock_price")
                        print("Found price element")
                        
                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        price_div = soup.find('p', {'id': 'stock_price'})
                        
                        print(f"Price div content: {price_div}")
                        
                        if price_div:
                            price_text = price_div.text.strip()
                            embed = discord.Embed(
                                title=f"RS3 Price Check: {item_name}",
                                color=discord.Color.gold()
                            )
                            embed.add_field(name="Current Price", value=price_text if price_text else "Price not available")
                            embed.set_footer(text="Data from ely.gg")
                        else:
                            embed = discord.Embed(
                                title="Error",
                                description="Could not find price information",
                                color=discord.Color.red()
                            )
                    else:
                        embed = discord.Embed(
                            title="Error",
                            description="Item not found, no support for acronyms etc yet.",
                            color=discord.Color.red()
                        )
                    
                    # The typing indicator will stay until this message is sent
                    await ctx.send(embed=embed)
                    
                finally:
                    driver.quit()
                
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                error_embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch price data",
                    color=discord.Color.red()
                )
                # Even on error, typing indicator will stay until message is sent
                await ctx.send(embed=error_embed)

    @check_price.error
    async def price_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            async with ctx.typing():
                await ctx.send("Please provide an item name. Usage: `,price <item name>`")

async def setup(bot):
    await bot.add_cog(RunescapePrices(bot))
