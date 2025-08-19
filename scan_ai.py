"""
AI string checker: scans all .py files under a folder,
extracts strings in quotes, and asks ChatGPT if any look awkward or wrong.

Before running, install `openai`:
    pip install openai

Then run with:
    python3 scan_ai.py
"""

import os
import re
import openai

# --- CONFIG ---
ROOT_FOLDER = r"U:\DISCORD BOT"
MODEL = "gpt-3.5-turbo"
# --------------

pattern = re.compile(r'(?<!\\)(?:\\\\)*([\'"])(.*?)(?<!\\)\1')

def ask_ai(s):
    prompt = (
        "Check the following UI string for grammar or spelling mistakes.\n"
        "If it sounds correct, respond EXACTLY with: OK\n"
        "Otherwise respond with a corrected version ONLY:\n\n"
        f"{s}"
    )
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def main():
    openai.api_key = input("Enter your OpenAI API key: ").strip()

    for dpath, dnames, fnames in os.walk(ROOT_FOLDER):
        for fname in fnames:
            if fname.endswith(".py"):
                fpath = os.path.join(dpath, fname)
                with open(fpath, encoding="utf-8") as f:
                    code = f.read()

                strings = pattern.findall(code)
                if not strings:
                    continue

                print(f"\n=== {fpath} ===")
                for _, text in strings:
                    if not text.strip():
                        continue
                    feedback = ask_ai(text)
                    if feedback != "OK":
                        print(f"• Found: {text}")
                        print(f"  Suggest: {feedback}")

if __name__ == "__main__":
    main()
