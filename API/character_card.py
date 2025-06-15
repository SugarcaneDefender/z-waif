import json
import yaml
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

    except:
        zw_logging.update_debug_log("No visual character card found!")
