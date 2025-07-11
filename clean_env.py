import os
import re
from datetime import datetime

def clean_value(value):
    """Clean a value by removing any obvious corruption."""
    # Handle special cases first
    if not value:
        return value
        
    # If it's a path, port, or URL, preserve it carefully
    if re.match(r'^[a-zA-Z]:\\', value) or re.match(r'^[\d.:]+$', value) or re.match(r'^https?://', value):
        return value.split()[0]  # Take only the first part if split by space
        
    # If it's a known boolean value
    if value.upper() in ['ON', 'OFF', 'TRUE', 'FALSE']:
        return value
        
    # If it's a number (including decimals)
    if re.match(r'^\d+\.?\d*$', value):
        return value
        
    # For other values, aggressively clean
    # Keep only alphanumeric, spaces, and basic punctuation
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-_.:/@\\]', '', value)
    # Remove any trailing garbage (common in corrupted files)
    cleaned = re.split(r'[^a-zA-Z0-9\-_.:/ \\]+', cleaned)[0]
    # Remove any leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def clean_env_file():
    """Clean and validate the .env file."""
    if not os.path.exists('.env'):
        print("No .env file found!")
        return

    # Create backup
    backup_name = f'.env.backup_clean_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    with open('.env', 'r', encoding='utf-8') as src, open(backup_name, 'w', encoding='utf-8') as dst:
        dst.write(src.read())
    print(f"Created backup: {backup_name}")

    # Read and clean
    settings = {}
    comments = []
    current_section = None

    print("\nCleaning settings...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f.readlines(), 1):
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                comments.append(line)
                if '===' in line:
                    current_section = line
            else:
                if '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        original_value = value.strip()
                        cleaned_value = clean_value(original_value)
                        
                        if key and cleaned_value:  # Only store if both key and value are non-empty
                            if cleaned_value != original_value:
                                print(f"Line {line_num}: Cleaned value for {key}")
                                print(f"  Original: {original_value}")
                                print(f"  Cleaned:  {cleaned_value}")
                            settings[key] = cleaned_value
                    except Exception as e:
                        print(f"Error parsing line {line_num}: {line}")
                        print(f"Error details: {str(e)}")

    # Write cleaned file
    with open('.env', 'w', encoding='utf-8') as f:
        current_section = None
        
        for line in comments:
            if '===' in line and line != current_section:
                f.write('\n' if current_section else '')
                current_section = line
            f.write(f"{line}\n")

        # Write all settings that have values
        for key, value in settings.items():
            f.write(f"{key}={value}\n")

    print("\nCleaning complete!")
    print(f"Found and cleaned {len(settings)} settings")
    print(f"Original file backed up as: {backup_name}")

if __name__ == "__main__":
    clean_env_file() 