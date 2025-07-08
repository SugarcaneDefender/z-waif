import re
from utils import zw_logging

# Quick lil function to check if any keywords are in a piece of text
def keyword_check(phrase: str, keywords: list[str]):
    for k in keywords:
        if str.lower(k) in str.lower(phrase):
            return True

    return False

# Checks for repetitions at the end of strings, and removes them (mainly for Whisper)
def old_remove_repeats(input_string: str):

    # Remove ending space if it exists
    if input_string != "" and input_string[-1] == " ":
        input_string = input_string[0:-1]

    list_split = re.split('[.!?,]', input_string)

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
        new_string = new_string.replace(list_split[-2] + ",", "")
        zw_logging.update_debug_log("Removed repeats! Original message was: " + input_string)
        return new_string

def remove_repeats(input_string: str):

    # Remove ending space if it exists
    if input_string != "" and input_string[-1] == " ":
        input_string = input_string[0:-1]

    repeat_detected = False
    detected_repeat_string = "None!"
    repeat_check_size = 3     # Base value, start with a third so we go biggest first

    while repeat_check_size < int(len(input_string) / 2.9) and not repeat_detected:        # Check until the size is too small, 3 repeats needed
        repeat_count = 0
        this_stringbit = input_string[len(input_string) - repeat_check_size:len(input_string)]
        # print("This sting bit is " + this_stringbit)

        # Check repetition on backpat
        this_checkpoint_marker = len(input_string) - repeat_check_size
        smalloop_repeat_found = True
        while (this_checkpoint_marker - repeat_check_size) > 0 and not repeat_detected and smalloop_repeat_found:
            # Check, add to the repeat count if detected
            # print(input_string[this_checkpoint_marker - repeat_check_size:this_checkpoint_marker])
            if this_stringbit == input_string[this_checkpoint_marker - repeat_check_size:this_checkpoint_marker]:
                repeat_count += 1
                smalloop_repeat_found = True
                # print("Small repeat found!")
            else:
                smalloop_repeat_found = False

            # If we are above the max repeat count (no more than 2 repeats), we have detected it!
            if repeat_count >= 2:
                repeat_detected = True
                # print("Repeat found!")
                detected_repeat_string = this_stringbit

            # Decrease checkpoint spot
            this_checkpoint_marker -= repeat_check_size


        # Make window smaller, repeat check loop
        repeat_check_size += 1


    if not repeat_detected:
        return input_string

    if repeat_detected:
        # Remove the others, and then add just one to the end
        new_string = input_string.replace(detected_repeat_string, "")
        new_string += detected_repeat_string

        zw_logging.update_debug_log("Removed repeats! Original message was: " + input_string)
        return new_string

