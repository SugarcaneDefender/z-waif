import logging
from datetime import datetime
import os
import time
from functools import wraps
from typing import Callable, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger('app')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Add file handler
file_handler = logging.FileHandler('logs/app.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app_logger.addHandler(file_handler)

debug_log = "General Debug log will go here!\n\nAnd here!"
rag_log = "RAG log will go here!"
kelvin_log = "Live temperature randomness will go here!"

def track_response_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to track and log the response time of a function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        log_info(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

def log_startup():
    """Log application startup information"""
    app_logger.info("=" * 50)
    app_logger.info(f"Application starting at {datetime.now()}")
    app_logger.info("System initialization beginning...")

def log_info(message: str):
    """Log info level message"""
    app_logger.info(message)

def log_error(message: str):
    """Log error level message"""
    app_logger.error(message)
    update_debug_log(f"ERROR: {message}")

def update_debug_log(text: str):
    global debug_log
    debug_log += "\n" + str(text)

def update_rag_log(text: str):
    global rag_log
    rag_log += "\n" + str(text)

def clear_rag_log():
    global rag_log
    rag_log = ""

def update_kelvin_log(text: str):
    global kelvin_log
    kelvin_log = text

def log_message_length_warning(message: str, length: int, type_str: str):
    """Log warning about message length"""
    if length < 10:
        warning = f"Message too short ({length} chars): {message[:50]}..."
        log_error(warning)
        update_debug_log(warning)
    elif length > 2000:
        warning = f"Message too long ({length} chars): {message[:50]}..."
        log_error(warning)
        update_debug_log(warning)

def log_stream_status(enabled: bool):
    """Log streaming status changes"""
    status = "enabled" if enabled else "disabled"
    log_info(f"Streaming mode {status}")
    update_debug_log(f"Streaming mode {status}")
