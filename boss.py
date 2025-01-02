import random
import json
import os

SAVE_FILE = "boss_drops.json"

def add_drops():
    """Allows the user to input drops and their drop rates (e.g., 'Pet 2/400')."""
    drops = {}
    print("Enter the boss drops and their drop rates (e.g., 'Pet 2/400'). Type 'done' when finished.")
    while True:
        user_input = input("Enter drop and rate: ").strip()
        if user_input.lower() == 'done':
            break
        try:
            drop_name, rate = user_input.split()
            numerator, denominator = map(int, rate.split('/'))
            if numerator <= 0 or denominator <= 0:
                raise ValueError
            drops[drop_name] = numerator / denominator
        except ValueError:
            print("Invalid input. Format must be 'DropName Numerator/Denominator'. Both numbers must be positive.")
    return drops

def edit_drop_rate():
    """Allows editing of existing boss drop rates."""
    if not os.path.exists(SAVE_FILE):
        print("No saved bosses found.")
        return

    with open(SAVE_FILE, 'r') as file:
        drops = json.load(file)

    if not drops:
        print("No saved bosses found.")
        return

    # Show available bosses
    print("\nAvailable bosses:")
    for boss in drops.keys():
        print(f"- {boss}")
    
    # Select boss
    boss_name = input("\nEnter boss name to edit: ").strip()
    if boss_name not in drops:
        print("Boss not found!")
        return
    
    # Show items for selected boss
    print(f"\nItems for {boss_name}:")
    for item, rate in drops[boss_name].items():
        # Convert decimal to fraction for display
        decimal = rate
        for denominator in range(1, 10001):  # Check denominators up to 10000
            numerator = round(decimal * denominator)
            if abs(numerator/denominator - decimal) < 1e-10:
                print(f"- {item}: {numerator}/{denominator}")
                break
    
    # Select item to edit
    item_name = input("\nEnter item name to edit: ").strip()
    if item_name not in drops[boss_name]:
        print("Item not found!")
        return
    
    # Get new rate
    while True:
        try:
            rate_input = input("Enter new drop rate (e.g., 2/400): ").strip()
            numerator, denominator = map(int, rate_input.split('/'))
            if numerator <= 0 or denominator <= 0:
                raise ValueError
            new_rate = numerator / denominator
            break
        except ValueError:
            print("Invalid input. Format must be 'Numerator/Denominator'. Both numbers must be positive.")
    
    # Update the rate
    drops[boss_name][item_name] = new_rate
    
    # Save changes
    with open(SAVE_FILE, 'w') as file:
        json.dump(drops, file, indent=4)
    print(f"\nSuccessfully updated {item_name} drop rate for {boss_name}")

def simulate_kills(drops, kill_count):
    """Simulates boss kills and records drops."""
    results = {drop: 0 for drop in drops}
    for _ in range(kill_count):
        for drop, rate in drops.items():
            if random.random() < rate:
                results[drop] += 1
    return results

def display_results(results, kill_count):
    """Displays the simulation results."""
    print(f"\nSimulation Results for {kill_count} kills:")
    for drop, count in results.items():
        percentage = (count / kill_count) * 100
        print(f"{drop}: {count} drops ({percentage:.2f}%)")

def save_drops(boss_name, drops):
    """Saves the drops for a boss."""
    data = {}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)

    data[boss_name] = drops
    with open(SAVE_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Drops for boss '{boss_name}' saved successfully!")

def load_drops():
    """Loads saved drops."""
    if not os.path.exists(SAVE_FILE):
        print("No saved bosses found.")
        return None, {}

    with open(SAVE_FILE, 'r') as file:
        data = json.load(file)

    if not data:
        print("No saved bosses found.")
        return None, {}

    print("\nSaved bosses:")
    for boss_name in data:
        print(f"- {boss_name}")

    boss_name = input("Enter the boss name to load (or type 'cancel' to go back): ").strip()
    if boss_name in data:
        return boss_name, data[boss_name]
    else:
        print("Boss not found.")
        return None, {}

def main():
    print("Boss Drop Simulation")
    while True:
        print("\n1. Add drops manually")
        print("2. Load a saved boss")
        print("3. Edit existing drop rates")
        print("4. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            drops = add_drops()
            boss_name = input("Enter the boss name: ").strip()
            if boss_name and drops:
                save_option = input(f"Do you want to save the drops for boss '{boss_name}'? (yes/no): ").strip().lower()
                if save_option == 'yes':
                    save_drops(boss_name, drops)
            break
        elif choice == '2':
            boss_name, drops = load_drops()
            if drops:
                print(f"Drops for boss '{boss_name}' loaded successfully!")
                break
        elif choice == '3':
            edit_drop_rate()
            continue
        elif choice == '4':
            print("Goodbye!")
            return
        else:
            print("Invalid choice. Please select a valid option.")

    if not drops:
        print("No drops entered or loaded. Exiting.")
        return

    while True:
        try:
            kill_count = int(input("Enter the number of kills to simulate: "))
            if kill_count <= 0:
                raise ValueError
        except ValueError:
            print("Invalid input. Kill count must be a positive integer.")
            continue

        results = simulate_kills(drops, kill_count)
        display_results(results, kill_count)

        replay = input("\nWould you like to run another simulation with the same boss? (yes/no): ").strip().lower()
        if replay != 'yes':
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
