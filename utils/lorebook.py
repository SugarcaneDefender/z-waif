import utils.cane_lib
import json
import utils.logging

do_log_lore = True
total_lore_default = "Here is some lore about the current topic from your lorebook;\n\n"


# Load the LORE_BOOK, it is now JSON configurable!
with open("Configurables/Lorebook.json", 'r') as openfile:
    LORE_BOOK = json.load(openfile)


# For retreival
# def lorebook_check(message):
#     global LORE_BOOK
#
#     # Lockout clearing
#     for lore in LORE_BOOK:
#         if lore['2'] > 0:
#             lore['2'] -= 1
#
#     # Search for new ones
#     for lore in LORE_BOOK:
#         if utils.cane_lib.keyword_check(message, [" " + lore['0']]) and lore['2'] == 0:
#             # Set our lockout
#             lore['2'] += 9
#
#             # Make our info
#
#             combo_lore = lore['0'] + ", " + lore['1']
#
#             return combo_lore
#
#     return "No lore!"

# Gathers ALL lore in a given scope (send in the message being sent, as well as any message pairs you want to check)
def lorebook_gather(messages, sent_message):

    # gather, gather, into reformed
    reformed_messages = [sent_message, ""]

    for message in messages:
        reformed_messages.append(message[0])
        reformed_messages.append(message[1])

    # gather all of our lore in one spot
    total_lore = total_lore_default

    # Reset all lore entry cooldown
    for lore in LORE_BOOK:
        lore['2'] = 0

    # Search every lore entry for each of the messages, and add the lore as needed
    for message in reformed_messages:
        # Search for new ones
        for lore in LORE_BOOK:
            if utils.cane_lib.keyword_check(message, [" " + lore['0'] + " ", " " + lore['0'] + "\'", " " + lore['0'] + "s",
                                                      " " + lore['0'] + "!", " " + lore['0'] + ".", " " + lore['0'] + ",", " " + lore['0'] + "!",
                                                      ]) and lore['2'] == 0:

                total_lore += (lore['0'] + ", " + lore['1'] + "\n\n")
                lore['2'] = 7   # lore has procced, prevent dupes

    if do_log_lore and total_lore != total_lore_default:
        utils.logging.update_debug_log(total_lore)


    return total_lore



# Check if keyword is in the lorebook
def rag_word_check(word):
    # Lockout clearing
    for lore in LORE_BOOK:
        if str.lower(lore['0']) == word:
            return True

    return False

