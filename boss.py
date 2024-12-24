import random

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
            drops[drop_name] = numerator / denominator
        except ValueError:
            print("Invalid input. Format must be 'DropName 1/Rate'.")
    return drops

def simulate_kills(drops, kill_count):
    """Simulates boss kills and records drops."""
    results = {drop: 0 for drop in drops}
    for _ in range(kill_count):
        for drop, rate in drops.items():
            if random.random() < rate:
                results[drop] += 1
    return results

def main():
    print("Boss Drop Simulation")
    drops = add_drops()
    if not drops:
        print("No drops entered. Exiting.")
        return

    kill_count = 1000
    results = simulate_kills(drops, kill_count)

    print(f"\nSimulation Results for {kill_count} kills:")
    for drop, count in results.items():
        print(f"{drop}: {count}")

if __name__ == "__main__":
    main()
