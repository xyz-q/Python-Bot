import math

def create_circular_progress_bar(self, percent, radius=5):
    """Create a circular progress bar using ASCII art."""
    percent = max(0, min(100, percent))
    angle = 2 * math.pi * (percent / 100)
    filled = int(angle // (math.pi / 2))
    empty = 4 - filled
    return f"[{'■' * filled}{'□' * empty}]"

print(create_circular_progress_bar(None, 50))
