import logging
from datetime import datetime
import os
import traceback
from logging.handlers import RotatingFileHandler
import sys

# Always resolve logs directory relative to this file's location
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# Create logs directory if it doesn't exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOGS_DIR, 'app.log')
app_logger = logging.getLogger('app')
app_logger.setLevel(logging.INFO)

# Remove any existing handlers to avoid duplicates
for handler in app_logger.handlers[:]:
    app_logger.removeHandler(handler)

# Add file handler with rotation
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app_logger.addHandler(file_handler)

# Global log variables for UI display
debug_log = "General Debug log will go here!\n\nAnd here!"
rag_log = "RAG log will go here!"
kelvin_log = "Live temperature randomness will go here!"

def log_startup():
    """Log application startup information"""
    try:
        app_logger.info("=" * 50)
        app_logger.info(f"Application starting at {datetime.now()}")
        app_logger.info(f"Log file: {log_file}")
        app_logger.info("System initialization beginning...")
        update_debug_log("System startup initiated")
    except Exception as e:
        print(f"Error in log_startup: {str(e)}", file=sys.stderr)

def log_info(message: str):
    """Log info level message"""
    try:
        app_logger.info(message)
        update_debug_log(f"INFO: {message}")
    except Exception as e:
        print(f"Error logging info: {str(e)}", file=sys.stderr)

def log_error(message: str):
    """Log error level message with full traceback"""
    try:
        app_logger.error(message)
        error_traceback = traceback.format_exc()
        if error_traceback != "NoneType: None\n":
            app_logger.error(error_traceback)
            update_debug_log(f"ERROR: {message}\n{error_traceback}")
        else:
            update_debug_log(f"ERROR: {message}")
    except Exception as e:
        print(f"Error logging error: {str(e)}", file=sys.stderr)

def update_debug_log(text: str):
    """Update the debug log with new text"""
    try:
        global debug_log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        debug_log += f"\n[{timestamp}] {str(text)}"
        # Keep debug log at a reasonable size
        if len(debug_log) > 10000:
            debug_log = debug_log[-10000:]
    except Exception as e:
        print(f"Error updating debug log: {str(e)}", file=sys.stderr)

def update_rag_log(text: str):
    """Update the RAG log with new text"""
    try:
        global rag_log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rag_log += f"\n[{timestamp}] {str(text)}"
        # Keep RAG log at a reasonable size
        if len(rag_log) > 10000:
            rag_log = rag_log[-10000:]
    except Exception as e:
        print(f"Error updating RAG log: {str(e)}", file=sys.stderr)

def clear_rag_log():
    """Clear the RAG log"""
    try:
        global rag_log
        rag_log = ""
    except Exception as e:
        print(f"Error clearing RAG log: {str(e)}", file=sys.stderr)

def update_kelvin_log(text: str):
    """Update the Kelvin log with new text"""
    try:
        global kelvin_log
        kelvin_log = text
    except Exception as e:
        print(f"Error updating Kelvin log: {str(e)}", file=sys.stderr)

def log_message_length_warning(message: str, length: int, type_str: str):
    """Log warning about message length"""
    try:
        if length < 10:
            warning = f"Message too short ({length} chars): {message[:50]}..."
            log_error(warning)
        elif length > 2000:
            warning = f"Message too long ({length} chars): {message[:50]}..."
            log_error(warning)
    except Exception as e:
        print(f"Error logging message length warning: {str(e)}", file=sys.stderr)

def log_stream_status(enabled: bool):
    """Log streaming status changes"""
    try:
        status = "enabled" if enabled else "disabled"
        log_info(f"Streaming mode {status}")
    except Exception as e:
        print(f"Error logging stream status: {str(e)}", file=sys.stderr)

# Test logging on module import
log_startup()
