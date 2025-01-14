import random
import asyncio

class SlotMachineTest:
    def __init__(self):
        # Define the symbols and their associated multipliers for payouts
        self.symbols = {
            "🎉": {"multiplier": 50, "name": "Jackpot"},
            "💎": {"multiplier": 25, "name": "Diamond"},
            "💰": {"multiplier": 15, "name": "Money Bag"},
            "🍒": {"multiplier": 10, "name": "Cherries"},
            "7️⃣": {"multiplier": 7, "name": "Seven"},
            "🍇": {"multiplier": 5, "name": "Clover"},
            "🔔": {"multiplier": 2.5, "name": "Star"},
            "🍊": {"multiplier": 1, "name": "Dice"}
        }
        
        self.symbol_list = list(self.symbols.keys())
        
        # Probabilities for outcomes (adjust as needed)
        self.probabilities = {
            "loss": 0.68,  # 68% chance of no match
            "two_of_a_kind": 0.27,  # 27% chance of two of a kind
            "three_of_a_kind": 0.05  # 5% chance of three of a kind (jackpot)
        }

    def generate_symbols(self):
        # Use a random value to determine the result type
        rng = random.random()
        
        # Determine result based on probability ranges
        if rng < self.probabilities["three_of_a_kind"]:
            # 5% chance for jackpot (three of a kind)
            symbol = random.choice(self.symbol_list)
            return [symbol, symbol, symbol]
        elif rng < self.probabilities["three_of_a_kind"] + self.probabilities["two_of_a_kind"]:
            # 27% chance for two of a kind
            symbol = random.choice(self.symbol_list)
            match_positions = random.sample([0, 1, 2], 2)  # Choose two positions to match
            result = []
            for i in range(3):
                if i in match_positions:
                    result.append(symbol)
                else:
                    # Choose a different symbol for the third position
                    remaining_symbols = [s for s in self.symbol_list if s != symbol]
                    result.append(random.choice(remaining_symbols))
            return result
        else:
            # 68% chance for no match (loss)
            return random.sample(self.symbol_list, 3)  # Pick 3 random symbols from the list

    async def run_test(self, test_count=100):
        results = {
            "losses": 0,
            "twos": 0,
            "threes": 0
        }

        for _ in range(test_count):
            final_symbols = self.generate_symbols()

            # Calculate matches
            symbol_counts = {}
            for symbol in final_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            max_matches = max(symbol_counts.values())

            if max_matches == 3:
                results["threes"] += 1
            elif max_matches == 2:
                results["twos"] += 1
            else:
                results["losses"] += 1
        
        print(f"Test Results after {test_count} spins:")
        print(f"Losses (No match): {results['losses']}")
        print(f"Two of a kinds: {results['twos']}")
        print(f"Three of a kinds: {results['threes']}")

# Example async run
async def main():
    test_machine = SlotMachineTest()
    await test_machine.run_test(100)

# Run the async test
asyncio.run(main())
