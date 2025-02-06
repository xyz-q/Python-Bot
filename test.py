from PIL import Image
import requests
from io import BytesIO
import itertools

DISTRICT_IMAGES = {
    "Amlodd": "https://runescape.wiki/images/Amlodd_Clan.png?6c04f",
    "Cadarn": "https://runescape.wiki/images/Cadarn_Clan.png?f8c96",
    "Crwys": "https://runescape.wiki/images/Crwys_Clan.png?49be0",
    "Hefin": "https://runescape.wiki/images/Hefin_Clan.png?e62c8",
    "Iorwerth": "https://runescape.wiki/images/Iorwerth_Clan.png?6d35e",
    "Ithell": "https://runescape.wiki/images/Ithell_Clan.png?95c05",
    "Meilyr": "https://runescape.wiki/images/Meilyr_Clan.png?6a5e9",
    "Trahaearn": "https://runescape.wiki/images/Trahaearn_Clan.png?9b997"
}

def combine_images(district1, district2):
    # Download images
    response1 = requests.get(DISTRICT_IMAGES[district1])
    response2 = requests.get(DISTRICT_IMAGES[district2])
    
    img1 = Image.open(BytesIO(response1.content))
    img2 = Image.open(BytesIO(response2.content))
    
    # Convert to RGBA
    img1 = img1.convert('RGBA')
    img2 = img2.convert('RGBA')
    
    # Make them the same height
    target_height = 75
    img1 = img1.resize((int(img1.width * target_height / img1.height), target_height))
    img2 = img2.resize((int(img2.width * target_height / img2.height), target_height))
    
    # Create new image with spacing
    spacing = 10
    combined_width = img1.width + spacing + img2.width
    combined_img = Image.new('RGBA', (combined_width, target_height), (0, 0, 0, 0))
    
    # Paste images
    combined_img.paste(img1, (0, 0))
    combined_img.paste(img2, (img1.width + spacing, 0))
    
    return combined_img

def create_all_combinations():
    # Get all possible combinations
    combinations = list(itertools.combinations(DISTRICT_IMAGES.keys(), 2))
    
    print(f"Creating {len(combinations)} combinations...")
    
    # Create a directory for the images if it doesn't exist
    import os
    if not os.path.exists('vos_combinations'):
        os.makedirs('vos_combinations')
    
    # Process each combination
    for district1, district2 in combinations:
        try:
            print(f"Processing: {district1} + {district2}")
            combined = combine_images(district1, district2)
            filename = f"vos_combinations/{district1}_{district2}.png"
            combined.save(filename)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Error processing {district1} + {district2}: {e}")

if __name__ == "__main__":
    create_all_combinations()
