import os
import re
from pathlib import Path

def find_emojis_in_file(file_path):
    # Emoji pattern for matching
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            emojis = emoji_pattern.findall(content)
            
            if emojis:
                return {
                    'file': str(file_path),
                    'emojis': emojis,
                    'count': len(emojis)
                }
    except Exception as e:
        return {
            'file': str(file_path),
            'error': str(e)
        }
    
    return None

def scan_folder_for_emojis(folder_path, recursive=True, file_extensions=None):
    folder_path = Path(folder_path)
    results = []
    
    # Default to common text file extensions if none specified
    if file_extensions is None:
        file_extensions = ['.txt', '.py', '.js', '.html', '.css', '.md']
    
    # Convert extensions to lowercase for case-insensitive comparison
    file_extensions = [ext.lower() for ext in file_extensions]
    
    # Choose between recursive or non-recursive file search
    if recursive:
        files = folder_path.rglob('*')
    else:
        files = folder_path.glob('*')
    
    # Scan each file
    for file_path in files:
        if file_path.is_file():
            # Check if file extension should be processed
            if file_path.suffix.lower() in file_extensions:
                result = find_emojis_in_file(file_path)
                if result:
                    results.append(result)
    
    return results

def print_results(results):
    total_emojis = 0
    files_with_emojis = 0
    emoji_frequency = {}
    
    print("\n=== Emoji Scan Results ===\n")
    
    # First pass: collect all emojis and count frequencies
    for result in results:
        if 'error' in result:
            print(f"Error in file {result['file']}: {result['error']}")
        else:
            files_with_emojis += 1
            total_emojis += result['count']
            
            # Count frequency of each emoji
            for emoji in result['emojis']:
                emoji_frequency[emoji] = emoji_frequency.get(emoji, 0) + 1
            
            print(f"\nFile: {result['file']}")
            print(f"Emoji count: {result['count']}")
            print(f"Emojis found: {' '.join(result['emojis'])}")
    
    # Sort emojis by frequency (most common first)
    sorted_emojis = sorted(emoji_frequency.items(), key=lambda x: x[1], reverse=True)
    
    print("\n=== Emoji Frequency ===")
    for emoji, count in sorted_emojis:
        print(f"{emoji}: {count}")
    
    print("\n=== Summary ===")
    print(f"Files containing emojis: {files_with_emojis}")
    print(f"Total emojis found: {total_emojis}")
    print(f"Unique emojis found: {len(emoji_frequency)}")

# Example usage
if __name__ == "__main__":
    # Specify the folder to scan
    folder_to_scan = "u:/DISCORD BOT"  # Replace with your folder path
    
    # Specify which file extensions to scan
    extensions = ['.py', '.txt', '.json']
    
    # Perform the scan
    results = scan_folder_for_emojis(
        folder_to_scan,
        recursive=True,  # Set to False to avoid scanning subfolders
        file_extensions=extensions
    )
    
    # Print the results
    print_results(results)
