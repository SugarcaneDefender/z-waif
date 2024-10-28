import re
import utils.logging

# Quick lil function to check if any keywords are in a piece of text
def keyword_check(phrase, keywords):
    for k in keywords:
        if str.lower(k) in str.lower(phrase):
            return True

    return False

# Checks for repetitions at the end of strings, and removes them (mainly for Whisper)
def remove_repeats(input_string):

    list_split = re.split('[.!?]', input_string)

    repeat_count = 0
    repeat_detected = False
    step = len(list_split) - 2
    while step > 1:
        if list_split[step] == list_split[step - 1]:
            repeat_count += 1
            if repeat_count > 1:
                repeat_detected = True
            step -= 1
        else:
            step = 0

    if not repeat_detected:
        return input_string
    if repeat_detected:
        new_string = input_string.replace(list_split[-2] + ".", "")
        new_string = new_string.replace(list_split[-2] + "!", "")
        new_string = new_string.replace(list_split[-2] + "?", "")
        utils.logging.update_debug_log("Removed repeats! Original message was: " + input_string)
        return new_string
