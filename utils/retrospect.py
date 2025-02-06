import utils.based_rag
import random
import utils.logging
import os

from API import backend


summary_tokens_count = 310
search_point_size = 16

enable_debug = True
char_name: str = os.environ.get("CHAR_NAME", "") # Default name?
assert char_name is not ""


# remembers a random past event
def retrospect_random_mem_summary():
    history = utils.based_rag.history_database

    # find random point in history to think about (not including anything recently)
    search_point = random.randint(0, len(history) - 90)

    history_scope = history[search_point:search_point+search_point_size]
    retrospect_message: str = ("[System L] Can you please summarize all of these chat messages? These are previous memories that you, " + char_name +
                          ", have experienced. " +
                          "Feel free to focus on details that are of note or you find interest in.")

    if enable_debug:
        utils.logging.update_rag_log(history_scope)

    # Encode and send!
    pre_encoded_message = backend.encode_raw_new_api(history_scope, retrospect_message, search_point_size)
    backend.summary_memory_run(pre_encoded_message, retrospect_message)







#
# FUTURE PLANNED

# remember and summarize everything since the last daily rememberence

# remember and summarize the last [memory window] messages

# gather various memories on this subject, and summarize what you know



