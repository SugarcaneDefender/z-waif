# Standard library imports
import json
import os

# Third-party imports
import yaml

# Local imports - Utils modules
from utils import zw_logging

character_card = "No character card loaded!"
visual_character_card = "No character card loaded!"

def load_char_card():
    global character_card
    global visual_character_card

    # Load main character card
    with open("Configurables/CharacterCard.yaml", 'r') as infile:
        character_card_loder = yaml.load(infile, Loader=yaml.FullLoader)
        character_card = character_card_loder["Character Card"]

    # also load the visual
    try:
        with open("Configurables/CharacterCardVisual.yaml", 'r') as infile:
            visual_character_card_loder = yaml.load(infile, Loader=yaml.FullLoader)
            visual_character_card = visual_character_card_loder["Character Card Visual"]
    except Exception as e:
        zw_logging.update_debug_log(f"No visual character card found: {e}")

def get_character_name():
    """Get the character name from environment or character card"""
    try:
        # Try to get from environment first
        char_name = os.environ.get('CHAR_NAME')
        if char_name:
            return char_name
        
        # Try to extract from character card if loaded
        if character_card and character_card != "No character card loaded!":
            # Simple extraction - look for name patterns
            import re
            # Look for patterns like "You are [Name]" or "I am [Name]"
            patterns = [
                r"You are ([A-Z][a-z]+)",
                r"I am ([A-Z][a-z]+)",
                r"My name is ([A-Z][a-z]+)",
                r"I'm ([A-Z][a-z]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, character_card)
                if match:
                    return match.group(1)
        
        # Fallback to default
        return "Assistant"
    except Exception as e:
        zw_logging.update_debug_log(f"Error getting character name: {e}")
        return "Assistant"
