import logging
from datetime import datetime
import os
import traceback
from logging.handlers import RotatingFileHandler
import sys
import platform
import psutil

# Ensure UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Define border character and line
BORDER_CHAR = "═"
BORDER_LINE = BORDER_CHAR * 79

# Always resolve logs directory relative to this file's location
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
CRASH_DIR = os.path.join(LOGS_DIR, 'crashes')

# Create logs and crash directories if they don't exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CRASH_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(LOGS_DIR, 'app.log')
crash_file = os.path.join(CRASH_DIR, f'crash_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
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

# Add crash file handler
crash_handler = logging.FileHandler(crash_file, encoding='utf-8')
crash_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
crash_handler.setLevel(logging.ERROR)
app_logger.addHandler(crash_handler)

# Global log variables for UI display
debug_log = "General Debug log will go here!\n\nAnd here!"
rag_log = "RAG log will go here!"
kelvin_log = "Live temperature randomness will go here!"

def get_system_info():
    """Get detailed system information for crash reports"""
    try:
        info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'processor': platform.processor(),
            'memory': f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
            'available_memory': f"{psutil.virtual_memory().available / (1024**3):.1f}GB",
            'disk_usage': f"{psutil.disk_usage('/').free / (1024**3):.1f}GB free",
            'working_directory': os.getcwd()
        }
        return info
    except Exception as e:
        return {'error': f"Could not get system info: {str(e)}"}

def log_startup():
    """Log application startup information with enhanced system details"""
    try:
        sys_info = get_system_info()
        app_logger.info(BORDER_LINE)
        app_logger.info("                             Z-WAIF STARTUP")
        app_logger.info(BORDER_LINE)
        app_logger.info(f"Application starting at {datetime.now()}")
        app_logger.info(f"Log file: {log_file}")
        app_logger.info(f"Crash log file: {crash_file}")
        app_logger.info("System Information:")
        for key, value in sys_info.items():
            app_logger.info(f"  {key}: {value}")
        app_logger.info("System initialization beginning...")
        update_debug_log("System startup initiated")
        # Prune oversized/old crash logs on every startup
        _cleanup_crash_logs()
    except Exception as e:
        print(f"Error in log_startup: {str(e)}", file=sys.stderr)

def log_info(message: str):
    """Log info level message"""
    try:
        app_logger.info(message)
        update_debug_log(f"INFO: {message}")
    except Exception as e:
        print(f"Error logging info: {str(e)}", file=sys.stderr)

def log_error(message: str, include_traceback: bool = True):
    """Log error level message with enhanced error information"""
    try:
        # Get current memory usage
        memory_info = psutil.Process().memory_info()
        memory_usage = f"Memory: {memory_info.rss / 1024 / 1024:.1f}MB"
        
        # Format the error message
        error_info = f"ERROR: {message}\n{memory_usage}"
        
        # Get traceback if requested and available
        if include_traceback:
            error_traceback = traceback.format_exc()
            if error_traceback and error_traceback != "NoneType: None\n":
                error_info += f"\nTraceback:\n{error_traceback}"
        
        # Log to both app and crash logs
        app_logger.error(error_info)
        update_debug_log(error_info)
        
        # Write to crash log file directly for serious errors
        with open(crash_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{datetime.now()} - {error_info}\n")
            
    except Exception as e:
        print(f"Error logging error: {str(e)}", file=sys.stderr)

def log_crash(error: Exception, context: str = ""):
    """Log critical crash information with full system state"""
    try:
        # Get system state
        sys_info = get_system_info()
        memory_info = psutil.Process().memory_info()
        
        # Format crash report
        crash_info = [
            BORDER_LINE,
            "                               CRASH REPORT",
            BORDER_LINE,
            f"Error: {str(error)}",
            f"Context: {context}",
            "",
            "System State:",
            f"Memory Usage: {memory_info.rss / 1024 / 1024:.1f}MB",
            *[f"{key}: {value}" for key, value in sys_info.items()],
            "",
            "Traceback:",
            traceback.format_exc() or "No traceback available",
            BORDER_LINE
        ]
        
        # Log to both regular and crash logs
        crash_text = "\n".join(crash_info)
        app_logger.critical(crash_text)
        
        # Write to dedicated crash log
        with open(crash_file, 'a', encoding='utf-8') as f:
            f.write(crash_text + "\n")
            
        # Update debug log
        update_debug_log(f"CRASH: {str(error)}\nSee {crash_file} for details")
        
    except Exception as e:
        print(f"Error logging crash: {str(e)}", file=sys.stderr)

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
    global rag_log
    rag_log = "RAG log cleared!\n"

def update_kelvin_log(text: str):
    """Update the temperature randomness log"""
    try:
        global kelvin_log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        kelvin_log += f"\n[{timestamp}] {str(text)}"
        # Keep kelvin log at a reasonable size
        if len(kelvin_log) > 10000:
            kelvin_log = kelvin_log[-10000:]
    except Exception as e:
        print(f"Error updating kelvin log: {str(e)}", file=sys.stderr)

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

# Add helper to keep crash directory size under control

def _cleanup_crash_logs(max_total_mb: int = 100, max_files: int = 50):
    """Delete empty or oldest crash logs so that the crash folder stays small.

    Parameters
    ----------
    max_total_mb : int
        Maximum combined size of all crash logs before pruning (in MiB).
    max_files : int
        Maximum number of crash log files to keep.  Older files are deleted first.
    """
    try:
        crash_files = [os.path.join(CRASH_DIR, f) for f in os.listdir(CRASH_DIR) if f.lower().endswith('.log')]
        # Remove all 0-byte files immediately
        for path in crash_files:
            try:
                if os.path.getsize(path) == 0:
                    os.remove(path)
            except FileNotFoundError:
                pass  # Might have been removed already

        # Refresh the list after deleting empties
        crash_files = [os.path.join(CRASH_DIR, f) for f in os.listdir(CRASH_DIR) if f.lower().endswith('.log')]
        # Calculate total size (MiB)
        total_size_mb = sum(os.path.getsize(p) for p in crash_files) / (1024 * 1024)
        if len(crash_files) > max_files or total_size_mb > max_total_mb:
            # Sort by modification time (oldest first)
            crash_files.sort(key=lambda p: os.path.getmtime(p))
            while (len(crash_files) > max_files) or (total_size_mb > max_total_mb and crash_files):
                oldest = crash_files.pop(0)
                try:
                    os.remove(oldest)
                except FileNotFoundError:
                    pass
                # Recompute size after deletion
                total_size_mb = sum(os.path.getsize(p) for p in crash_files) / (1024 * 1024) if crash_files else 0
    except Exception as e:
        # Never let cleanup failure crash the app – just print a warning.
        print(f"[zw_logging] Crash-log cleanup failed: {e}", file=sys.stderr)

# Call cleanup once at import time so giant folders are trimmed even if log_startup() isn't used
_cleanup_crash_logs()

# Test logging on module import
log_startup()
