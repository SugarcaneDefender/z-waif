import API.Oogabooga_Api_Support
import string
import threading
import utils.lorebook
import random
import json
import os
import time
import utils.logging
import utils.settings

# Words and their data
word_database = {
    'word': ["", " ", "the", "it"],
    'count': [1, 1, 1, 1],
    'value': [0.0, 0.0, 0.0, 0.0],
    'total_word_count': 0
}

# Histories
histories_word_id_database = {
    'me': [],
    'her': [],
    'scores': []
}

history_database = [["Start of all history!", "Start of all history!"]]

show_rag_debug = True
show_rag_debug_deep = False

current_rag_message = "No memory currently!"

history_demarc = 20         # This is the point where the history gets considered as usable for RAG

manual_recalculate_ignore_latest = False
is_setting_up = True

char_name = os.environ.get("CHAR_NAME")


#
# Anyone who is wondering what this is for, this is a RAG, or Retrivial Agumented Generation system. A very basic one, at that.
# It basically extends the memory, pulling relevent past info. Can cause things to go 10% slower, but it really helps.
# I've had mine get many good recalls and memories, and it also helps to stablize outputs and style, pulling from the past.
# Enable once you have ~60 message pairs, or if you are importing. It fails gently if enabled to early =\(-.-
#

def setup_based_rag():

    if show_rag_debug:
        utils.logging.update_rag_log("Running BASED RAG")
        print("Running BASED RAG")

    # Create a word-value database(d)
    global word_database
    global manual_recalculate_ignore_latest
    global is_setting_up
    global history_database

    #
    # IMPLEMENT SMART THREADING: Split it per thread and continually grab next order
    #

    #
    # HISTORY LOGS
    #

    for file in os.listdir("Logs/"):
        if file.endswith(".json") and file.startswith("ChatLog"):
            with open("Logs/" + file, 'r') as openfile:
                temp_hist = json.load(openfile)
                history_database += temp_hist

        else:
            continue


    # Import Current History As Well
    history_database += API.Oogabooga_Api_Support.ooga_history


    #
    # LIVE HISTORY
    #

    # Main loop that will run through and count all uses of a given word
    # Thread this as well eventually
    i = 0
    while i < len(history_database):

        # Add in each message pair
        parse_words_to_database(history_database[i][0], 0)
        parse_words_to_database(history_database[i][1], 1)

        i = i + 1



    # Calculate the values of all words
    # Thread this as well eventually

    calc_word_values()



    # Clear out any common words from the database index, for searching purposes
    # Thread this as well eventually
    i = 0
    while i < len(histories_word_id_database["me"]):
        prune_common(i)
        i = i + 1


    # Flag us so we don't add latest message in
    manual_recalculate_ignore_latest = True


    # Flag this as done
    is_setting_up = False


    # Print out so we can see if the word database is working
    if show_rag_debug_deep:
        utils.logging.update_rag_log(word_database)
        utils.logging.update_rag_log(histories_word_id_database)




def run_based_rag(message, her_previous):

    global word_database

    # Blocking statement to stop if our RAG is not enabled
    if not utils.settings.rag_enabled:
        return

    # Clear the log, a new operation is beginning
    utils.logging.clear_rag_log()

    #
    # EVALUATE OUR SENT ONES FIRST
    #

    # Parse the message being sent
    history_word_ids = parse_words_to_database(message, 2)
    history_word_scores = []


    # Check the score value of all words
    # NOTE: This is a maintenance item that doesn't need to run every time, so we just do it randomly

    random_recalc = random.randint(0, 100)
    if random_recalc > 70:
        calc_word_values()


    # Run evaluation now that we have all of the words
    i = 0
    while i < len(history_word_ids):

        # Pair all word keys with scores
        score = word_database['value'][history_word_ids[i]]

        # Boost lore word score (only single word)
        if utils.lorebook.rag_word_check(word_database['word'][history_word_ids[i]]):
            score = (score + 1) / 2

        history_word_scores.append(score)

        i = i + 1

    # Local variable, to control cutoff
    history_word_ids_feed_demarc = i


    #
    # EVALUATE HER SENT ONES SECOND
    #

    hers_history_word_ids = parse_words_to_database(her_previous, 3)


    # Run evaluation now that we have all of the words

    i = 0
    while i < len(hers_history_word_ids):

        # Pair all word keys with scores
        score = word_database['value'][hers_history_word_ids[i]]

        # Boost lore word score (only single word)
        if utils.lorebook.rag_word_check(word_database['word'][hers_history_word_ids[i]]):
            score = (score + 1) / 2

        history_word_ids.append(hers_history_word_ids[i])
        history_word_scores.append(score * 0.97)            # Make hers less powerful

        i = i + 1




    # Get the top six scoring words, in order
    highest_scores = [0, 0, 0, 0, 0, 0]
    highest_score_keys = [0, 0, 0, 0, 0, 0]
    highest_score_ids = [0, 0, 0, 0, 0, 0]

    j = 0
    her_word_topper = False
    her_word_count = 0
    while j < len(highest_scores):

        # Iterate to find highest scoring word, not including duplicates, and not including words with a perfect score
        i = 0

        while i < len(history_word_ids):
            if history_word_scores[i] > highest_scores[j] and not highest_score_ids.__contains__(history_word_ids[i]):
                highest_scores[j] = history_word_scores[i]
                highest_score_keys[j] = i
                highest_score_ids[j] = history_word_ids[i]

                # Controls for if she has added words
                if i > history_word_ids_feed_demarc:
                    her_word_topper = True
                else:
                    her_word_topper = False

            i = i + 1

            # If she is at her word limit, skip all her words
            if her_word_count >= 2 and i > history_word_ids_feed_demarc:
                i = len(history_word_ids)

        # Flag if the word we got was one of hers
        if her_word_topper:
            her_word_count += 1

        # Iterate to our next word, of course until we get to top 6 words
        j = j + 1

    # Output our highest scoring words
    if show_rag_debug:
        x = 0
        log_output_text = ""
        while x < len(highest_score_ids):
            log_output_text += str(word_database['word'][highest_score_ids[x]]) + "\n"
            x = x + 1

        utils.logging.update_rag_log(log_output_text)


    #
    # NOW EVALUATE ALL MESSAGE PAIRS AND SCORE THEM
    #


    # Evaluate
    i = 0
    while i < len(histories_word_id_database['me']):
        score_value = evaluate_message(highest_score_ids, histories_word_id_database['me'][i]) + evaluate_message(highest_score_ids, histories_word_id_database['her'][i])
        histories_word_id_database['scores'][i] = score_value
        i = i + 1


    # Print us out the best score & message

    i = 1                       # Disallow message 1; always start on message 2 or higher
    best_message_score = 0
    best_message_id = 0

    # Disallow any recalling from past the demarc. Should be able to recall / flow from there
    while i < len(histories_word_id_database['me']) - history_demarc:

        central_score = histories_word_id_database['scores'][i-1]
        central_score += histories_word_id_database['scores'][i]
        central_score += histories_word_id_database['scores'][i+1]

        # Less than or equal to makes it so that more recent entries are given a bigger score
        if best_message_score <= histories_word_id_database['scores'][i]:
            best_message_id = i
            best_message_score = histories_word_id_database['scores'][i]

        i = i + 1


    #
    #   Create for the current message!
    #

    global current_rag_message

    current_rag_message = "[System M]; This message is a memory of an interaction you have had, relevant to what is currently happening;\n"
    current_rag_message += "User: " + history_database[best_message_id - 1][0] + "\n"
    current_rag_message += char_name + ": " + history_database[best_message_id - 1][1] + "\n"
    current_rag_message += "User: " + history_database[best_message_id][0] + "\n"
    current_rag_message += char_name + ": " + history_database[best_message_id][1] + "\n"
    current_rag_message += "User: " + history_database[best_message_id + 1][0] + "\n"
    current_rag_message += char_name + ": " + history_database[best_message_id + 1][1] + "\n"
    current_rag_message += "[System M]; This is the end of the memory!"

    if show_rag_debug:
        utils.logging.update_rag_log(current_rag_message)



# Bit to actually receive what the RAG has to offer
def call_rag_message():
    return current_rag_message



def parse_words_to_database(message, flag):

    global word_database

    # Count, using a word collector to detect when spaces are gone
    i = 0
    word_collector = ""
    word_start_marker = 0
    history_word_ids = []


    # Decide if we want to add to the count, depending on the flag
    count_to_total = True

    if flag == 2 or flag == 3:
        count_to_total = False



    refined_message = message.translate(str.maketrans('', '', string.punctuation))
    refined_message = str.lower(refined_message)
    refined_message = refined_message.replace("\n", " ")

    if show_rag_debug_deep:
        utils.logging.update_rag_log(refined_message)


    while i < len(refined_message):

        if refined_message[i] == " ":
            word_start_marker = i + 1

        # Look for stopping, either spaces or end of message
        if i + 1 == len(refined_message) or refined_message[i+1] == ' ':

            # Feed our word collector the marked version
            word_collector = refined_message[word_start_marker:i+1]

            j = 0
            word_found = False

            # Scan if word is in database
            while j < len(word_database["word"]):
                if word_collector == word_database["word"][j]:

                    if count_to_total:
                        word_database["count"][j] = word_database["count"][j] + 1

                    word_found = True

                    # Add to our history word ID database
                    history_word_ids.append(j)

                j = j + 1


            # If word not in database and we are counting, add it in (word will simply be skipped for eval parsing)
            if not word_found and count_to_total:
                word_database["word"].append(word_collector)
                word_database["count"].append(1)
                word_database["value"].append(0.99)         # Note: will have to be recalculated later on for new words

                # Add to our history word ID database
                history_word_ids.append(len(word_database["word"]) - 1)


            # Set the marker for our next word
            word_start_marker = i + 2

            # Boost again to skip space
            i = i + 1


            # Clear the word
            word_collector = ""

            # Boost our total word count
            if count_to_total:
                word_database['total_word_count'] = word_database['total_word_count'] + 1



        i = i + 1

    # Sent by me, history
    if flag == 0:
        histories_word_id_database["me"].append(history_word_ids)

        return history_word_ids     # Not actually used, for error catchcase

    # Sent by her, history
    if flag == 1:
        histories_word_id_database["her"].append(history_word_ids)
        histories_word_id_database["scores"].append(0)              # Just here so we can score later

        return history_word_ids     # Not actually used, for error catchcase



    # Sent by me, live add/eval
    if flag == 2:
        return history_word_ids

    # Sent by her, live add/eval
    if flag == 3:
        return history_word_ids


# Calculates the value of all words
def calc_word_values():
    global word_database

    # Give base values to all the words, with a maximum score being 1
    i = 0
    while i < len(word_database["value"]):
        word_database['value'][i] = (1 / (word_database['count'][i] + 19)) * 20
        i = i + 1



# Prunes really common words, as there is no need to store these
def prune_common(point):

    global word_database
    global histories_word_id_database

    # Prunes the common words out of the given phrase
    i = 0
    while i < len(histories_word_id_database["me"][point]):
        word_id = histories_word_id_database["me"][point][i]
        if (word_database['count'][word_id] / word_database['total_word_count']) > 0.00077:
            histories_word_id_database["me"][point].pop(i)
            i = 0

        i = i + 1

    i = 0
    while i < len(histories_word_id_database["her"][point]):
        word_id = histories_word_id_database["her"][point][i]
        if (word_database['count'][word_id] / word_database['total_word_count']) > 0.00077:
            histories_word_id_database["her"][point].pop(i)
            i = 0

        i = i + 1


# Totals and returns the value of a given message, when tied to keywords
def evaluate_message(valued_word_ids, hist_word_ids):

    i = 0
    value = 0

    # Compares for each valued word, so it won't ever do repeats
    while i < len(valued_word_ids):
        if hist_word_ids.__contains__(valued_word_ids[i]):
            value = value + 1

        i = i + 1

    # Reduce the value of the statement if it is long, to avoid "fillabustering" (content getting picked via mass)
    value = value - (len(hist_word_ids) / 120)

    # Never less than 0
    if value < 0:
        value = 0


    return value


# Adds messages to the database once it becomes validated (on next message send)
def add_message_to_database():

    # Blocking statement to stop if our RAG is not enabled
    if not utils.settings.rag_enabled:
        return

    # Import History
    history = API.Oogabooga_Api_Support.ooga_history
    global word_database, manual_recalculate_ignore_latest, history_database

    # Do not add in if we just manually re-calculated, it is already in there
    if manual_recalculate_ignore_latest:
        manual_recalculate_ignore_latest = False
        return

    new_msg = len(history) - 1

    # Do not add in if the content is the same as the last message (likely bugged / undo)
    if (history[new_msg][0] + history[new_msg][1]) == (history_database[-1][0] + history_database[-1][1]):
        utils.logging.update_debug_log("Preventing dupe in RAG!")
        return


    # Ignore any system deletable messages, and just fall back until before it
    while history[new_msg][0].__contains__("[System D]"):
        new_msg = new_msg - 1

    # Add latest message pair, to both the word database AND local hist
    parse_words_to_database(history[new_msg][0], 0)
    parse_words_to_database(history[new_msg][1], 1)

    history_database += [[history[new_msg][0], history[new_msg][1]]]


    # Prune these as well (always latest one, may not sync 1:1 to history due to system messages)
    prune_common(len(histories_word_id_database['me']) - 1)



# Remove last entry in the database (undo)
def remove_latest_database_message():

    # Blocking statement to stop if our RAG is not enabled
    if not utils.settings.rag_enabled:
        return

    #
    # NOTE: Does NOT uncount words! This should mostly be fine in the large scale, and we still have manual recalcs that can self right this
    #

    global histories_word_id_database

    histories_word_id_database["me"].pop()
    histories_word_id_database["her"].pop()
    histories_word_id_database["scores"].pop()



def store_rag_history():

    # Blocking statement to stop if our RAG is not enabled
    if not utils.settings.rag_enabled:
        return

    # Save, Export to JSON
    with open("RAG_Database/LiveRAG_Words.json", 'w') as outfile:
        json.dump(word_database, outfile, indent=4)

    with open("RAG_Database/LiveRAG_HistoryWordID.json", 'w') as outfile:
        json.dump(histories_word_id_database, outfile, indent=4)

    with open("RAG_Database/LiveRAG_History.json", 'w') as outfile:
        json.dump(history_database, outfile, indent=4)


def load_rag_history():

    # Blocking statement to stop if our RAG is not enabled
    if not utils.settings.rag_enabled:
        return

    global word_database, histories_word_id_database, history_database, is_setting_up

    # Check if we need to load, or generate the RAG
    path = 'RAG_Database/LiveRAG_Words.json'
    path2 = 'RAG_Database/LiveRAG_HistoryWordID.json'
    path3 = 'RAG_Database/LiveRAG_History.json'

    check_file = os.path.isfile(path)
    check_file2 = os.path.isfile(path2)
    check_file3 = os.path.isfile(path3)


    # Switch
    if check_file and check_file2 and check_file3:

        # File found, load

        if show_rag_debug:
            utils.logging.update_rag_log("\nLoading RAG from pervious session!\n")

        with open(path, 'r') as openfile:
            word_database = json.load(openfile)

        with open(path2, 'r') as openfile:
            histories_word_id_database = json.load(openfile)

        with open(path3, 'r') as openfile:
            history_database = json.load(openfile)

        # Flag this as done
        is_setting_up = False

    else:

        # No file, set up

        manual_recalculate_database()


def manual_recalculate_database():

    # All in one

    print("\nManually re-calculating the RAG database. Give me some time...\n")
    utils.logging.update_rag_log("\nManually re-calculating the RAG database. Give me some time...\n")
    setup_based_rag()


def word_value_passive_calculation():

    # Passively recalculate word values in the background
    # NYI - Not yet implemented. Will need to be pretty smart

    while True:
        time.sleep(120)

        if not is_setting_up:
            calc_word_values()

