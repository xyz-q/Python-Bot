import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime

async def get_merchant_stock():
    """Get future merchant stock"""
    async with aiohttp.ClientSession() as session:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        future_items = []
        async with session.get('https://runescape.wiki/w/Travelling_Merchant%27s_Shop/Future', headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                table = soup.find('table', class_="wikitable sticky-header")
                if table:
                    rows = table.find_all('tr')[1:]
                    
                    for row in rows:
                        date_cell = row.find('td')
                        if date_cell:
                            date = date_cell.text.strip()
                            
                            items = []
                            inventory_cells = row.find_all('td', class_="inventory-image")
                            for cell in inventory_cells:
                                anchor = cell.find('a')
                                if anchor and anchor.get('title'):
                                    items.append(anchor['title'])
                            
                            if items:
                                future_items.append((date, items))

                future_items.reverse()
                
                print(f"Total days found: {len(future_items)}\n")
                
                for date, items in future_items:
                    print(f"{date}:")
                    for item in items:
                        print(f"- {item}")
                    print()

async def main():
    await get_merchant_stock()

if __name__ == "__main__":
    asyncio.run(main())
