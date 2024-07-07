import utils.cane_lib
import json


# Lore Entries Go Here

# Load the LORE_BOOK, it is now JSON configurable!
with open("Configurables/Lorebook.json", 'r') as openfile:
    LORE_BOOK = json.load(openfile)


# For retreival
def lorebook_check(message):
    global LORE_BOOK

    # Lockout clearing
    for lore in LORE_BOOK:
        if lore['2'] > 0:
            lore['2'] -= 1

    # Search for new ones
    for lore in LORE_BOOK:
        if utils.cane_lib.keyword_check(message, [" " + lore['0']]) and lore['2'] == 0:
            # Set our lockout
            lore['2'] += 9

            # Make our info

            combo_lore = lore['0'] + ", " + lore['1']

            return combo_lore

    return "No lore!"

# Check if keyword is in the lorebook
def rag_word_check(word):
    # Lockout clearing
    for lore in LORE_BOOK:
        if str.lower(lore['0']) == word:
            return True

    return False

