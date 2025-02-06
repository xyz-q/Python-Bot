import requests
from datetime import datetime
from colorama import init, Fore, Style

init()  # Initialize colorama

def get_vos_data():
    try:
        response = requests.get('https://api.weirdgloop.org/runescape/vos/history')
        response.raise_for_status()
        
        data = response.json()
        current_vos = data['data'][0]
        timestamp = datetime.fromisoformat(current_vos['timestamp'].replace('Z', '+00:00'))
        
        print(f"\n{Fore.CYAN}✨ Current Voice of Seren ✨{Style.RESET_ALL}")
        print(f"Time: {Fore.YELLOW}{timestamp.strftime('%Y-%m-%d %H:%M')} UTC{Style.RESET_ALL}")
        print(f"Districts: {Fore.GREEN}{current_vos['district1']}{Style.RESET_ALL} and {Fore.GREEN}{current_vos['district2']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Recent history:{Style.RESET_ALL}")
        for entry in data['data'][1:5]:
            time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            print(f"{Fore.YELLOW}{time.strftime('%H:%M UTC')}{Style.RESET_ALL}: "
                  f"{Fore.GREEN}{entry['district1']}{Style.RESET_ALL} and "
                  f"{Fore.GREEN}{entry['district2']}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error fetching VoS data: {e}{Style.RESET_ALL}")

# Run the function
get_vos_data()
