import json
import yaml

character_card = "No character card loaded!"

def load_char_card():
    global character_card

    with open("Configurables/CharacterCard.yaml", 'r') as infile:
        character_card_loder = yaml.load(infile, Loader=yaml.FullLoader)
        character_card = character_card_loder["Character Card"]
