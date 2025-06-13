debug_log = "General Debug log will go here!\n\nAnd here!"
rag_log = "RAG log will go here!"
kelvin_log = "Live temperature randomness will go here!"

from typing import Any
from utils.zw_logging import log_info as zw_log_info, log_error as zw_log_error

def update_debug_log(text: Any):
    global debug_log
    debug_log += "\n\n" + str(text)


def update_rag_log(text: Any):
    global rag_log
    rag_log += "\n\n" + str(text)

def clear_rag_log():
    global rag_log
    rag_log = ""

def update_kelvin_log(text: str):
    global kelvin_log
    kelvin_log = text

def log_info(message: str):
    zw_log_info(message)

def log_error(message: str):
    zw_log_error(message)
