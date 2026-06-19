import time

import utils.based_rag
import random
import API.api_controller
import utils.zw_logging
import os
import json

use_rolling_summaries = False

summary_tokens_max_count = 310
search_point_size = 10
search_point_current_count = 0

enable_debug = True
char_name = os.environ.get("CHAR_NAME")

live_summarization_log = []

# remembers a random past event
def retrospect_random_mem_summary():
    history = utils.based_rag.history_database

    # find random point in history to think about (not including anything recently)
    search_point = random.randint(0, len(history) - 90)

    history_scope = history[search_point:search_point+search_point_size]
    retrospect_message = ("[System L] Can you please summarize all of these chat messages? These are previous memories that you, " + char_name +
                          ", have experienced. " +
                          "Feel free to focus on details that are of note or you find interest in.")

    if enable_debug:
        utils.zw_logging.update_rag_log(history_scope)

    # Encode and send!
    pre_encoded_message = API.api_controller.encode_raw_new_api(history_scope, retrospect_message, search_point_size)
    API.api_controller.summary_memory_run_hard(pre_encoded_message, retrospect_message)


def retrospect_current_messages():
    global live_summarization_log

    if not utils.retrospect.use_rolling_summaries:
        return

    history = utils.based_rag.history_database

    # use a search point that is atleast 2 messages back to prevent issues
    search_point = len(history) - search_point_size - 2

    history_scope = history[search_point:search_point+search_point_size]
    retrospect_message = ("[System L] Can you please summarize all of these chat messages? These are previous memories that you, " + char_name +
                          ", have experienced. " +
                          "Feel free to focus on details that are of note or you find interest in. Try and note what is currently going on and what you are doing. Mention the most important things first, you have about a paragraph. " +
                          "Discuss any feelings or conclusions you have come to. Be sure to use keywords and proper nouns.")

    if enable_debug:
        utils.zw_logging.update_rag_log(history_scope)

    # Pause because breaking??
    time.sleep(0.2)

    # Encode and send!
    pre_encoded_message = API.api_controller.encode_raw_new_api(history_scope, retrospect_message, search_point_size)
    API.api_controller.regenerate_requests_count = 0        # limit the total number of regenerations
    API.api_controller.summary_memory_run_soft(pre_encoded_message, retrospect_message)

    # Pull out our summarization
    utils.zw_logging.update_debug_log(API.api_controller.receive_summary_via_oogabooga())
    #print(API.api_controller.receive_summary_via_oogabooga())

    # Save this & export to JSON
    live_summarization_log.append(API.api_controller.receive_summary_via_oogabooga())
    with open("LiveSummaryLog.json", 'w') as outfile:
        json.dump(live_summarization_log, outfile, indent=4)


    # TODO

    # Test if this works
    # Saving the logs
    # Feeding the most recent summary to all the API calls (via new encoder) so it work
        # Do NOT use the most recent one for regular calls, instead maybe use #2 and #3 summaries?
        # USE most recent one for making a new summary, #1 and #2
        # Where do I append XD

    # Summarizing all of the past history
        # A button to "re-jig" it and go through all the summary again
    # Make RAG optionally run off the summary history
    # .env and other configurables

def retrospect_past_messages():

    mambo = 1


def load_past_summaries():
    global live_summarization_log

    with open("LiveSummaryLog.json", 'r') as openfile:
        live_summarization_log = json.load(openfile)

    # Make a new backup of our LiveSummaryLog on each boot as well

    with open("Backups/LiveSummaryLogBackup.bak", 'w') as soutfile:
        json.dump(live_summarization_log, soutfile, indent=4)




#
# FUTURE PLANNED

# remember and summarize everything since the last daily rememberence

# remember and summarize the last [memory window] messages

# gather various memories on this subject, and summarize what you know



