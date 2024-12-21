import requests
from bs4 import BeautifulSoup

def get_merchant_items():
    # Get the wiki page
    url = "https://runescape.wiki/w/Travelling_Merchant%27s_Shop"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all td elements with class 'inventory-image'
    inventory_cells = soup.find_all('td', class_='inventory-image')
    
    # Store all items
    items = []
    
    for cell in inventory_cells:
        # Find the adjacent cell (next sibling) that contains the item name
        next_cell = cell.find_next_sibling('td')
        if next_cell:
            item_link = next_cell.find('a')
            if item_link and item_link.get('title'):
                item_name = item_link.get('title')
                if item_name and not item_name.isspace():
                    items.append(item_name)
    
    # Print formatted dictionary
    print("self.item_emojis = {")
    for item in sorted(set(items)):  # Using set to remove duplicates
        if item:  # Only print non-empty items
            print(f'    "{item}": "",  # Add emoji here')
    print('    "default": "📦"')
    print("}")

# Run the script
get_merchant_items()
