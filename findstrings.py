import re
import os

# change this folder to wherever you want to scan
ROOT_FOLDER = "U:\DISCORD BOT"

# regex to pick up "..." and '...' string literals
pattern = re.compile(r'(?<!\\)(?:\\\\)*([\'"])(.*?)(?<!\\)\1')

for dirpath, dirnames, filenames in os.walk(ROOT_FOLDER):
    for filename in filenames:
        if filename.endswith(".py"):
            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, encoding="utf-8") as f:
                    code = f.read()
                # extract strings
                strings = pattern.findall(code)
                if strings:
                    print(f"\n=== {full_path} ===")
                    for quote, text in strings:
                        print(f"   → {text}")
            except Exception as e:
                print(f"Could not read {full_path}: {e}")
