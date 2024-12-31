import random
import json
import os

SAVE_FILE = "boss_drops.json"

def add_drops():
    """Allows the user to input drops and their drop rates."""
    drops = {}
    print("Enter the boss drops and their drop rates (e.g., 'Pet 1/200'). Type 'done' when finished.")
    while True:
        user_input = input("Enter drop and rate: ").strip()
        if user_input.lower() == 'done':
            break
        try:
            drop_name, rate = user_input.split()
            numerator, denominator = map(int, rate.split('/'))
            if numerator != 1 or denominator <= 0:
                raise ValueError
            drops[drop_name] = numerator / denominator
        except ValueError:
            print("Invalid input. Format must be 'DropName 1/Rate'. Rate must be positive.")
    return drops

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
        return {}

    with open(SAVE_FILE, 'r') as file:
        data = json.load(file)

    if not data:
        print("No saved bosses found.")
        return {}

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
        choice = input("\nDo you want to (1) add drops manually, or (2) load a saved boss? ").strip()
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
        else:
            print("Invalid choice. Please select '1' or '2'.")

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
