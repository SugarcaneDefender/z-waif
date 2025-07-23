
debug_log = "General Debug log will go here!\n\nAnd here!"
rag_log = "RAG log will go here!"
kelvin_log = "Live temperature randomness will go here!"


def update_debug_log(text):
    global debug_log
    debug_log += "\n\n" + str(text)


def update_rag_log(text):
    global rag_log
    rag_log += "\n\n" + str(text)

def clear_rag_log():
    global rag_log
    rag_log = ""

def update_kelvin_log(text):
    global kelvin_log
    kelvin_log = text
