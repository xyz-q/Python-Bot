import math

def create_circular_progress_bar(self, percent, radius=5):
    """Create a circular progress bar using ASCII art."""
    percent = max(0, min(100, percent))  # Clamp between 0 and 100
    angle = 2 * math.pi * (percent / 100)  # Angle based on percent
    filled = int(angle // (math.pi / 2))  # Determine the filled quadrants
    empty = 4 - filled
    return f"[{'■' * filled}{'□' * empty}]"

# Example of usage:
print(create_circular_progress_bar(None, 50))
# Output: [■■□□]
