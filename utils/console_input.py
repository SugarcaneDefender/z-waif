import threading
import queue
import sys

# Thread-safe queue for incoming console lines
_input_queue: "queue.Queue[str]" = queue.Queue()
_print_queue: "queue.Queue[str]" = queue.Queue()
_current_input = ""

def _reader() -> None:
    """Block on stdin and push each entered line into the queue."""
    global _current_input
    while True:
        try:
            line = sys.stdin.readline()
            if not line:  # EOF encountered
                break
            _input_queue.put(line.rstrip("\r\n"))
            _current_input = ""  # Reset on enter
        except Exception as e:
            # Log stdin error but keep main app alive
            print(f"Console input error: {e}")
            break

def print_safe(message: str) -> None:
    """Queue a message to be printed safely to the console."""
    _print_queue.put(message)

def _process_print_queue():
    """Process all pending messages in the print queue."""
    while not _print_queue.empty():
        try:
            message = _print_queue.get_nowait()
            # Clear the current line, print the message, and redraw the prompt
            sys.stdout.write(f"\r{' ' * 80}\r")  # Clear line
            sys.stdout.write(f"{message}\n")
            sys.stdout.write(f"You > {_current_input}")
            sys.stdout.flush()
        except queue.Empty:
            break

def start_console_reader() -> None:
    """Spin up the background thread once; safe to call multiple times."""
    if getattr(start_console_reader, "_started", False):
        return
    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    start_console_reader._started = True  # type: ignore[attr-defined]

def get_line_nonblocking() -> str | None:
    """Return a queued console line if available, else None."""
    _process_print_queue() # Check for and print messages before getting input
    try:
        line = _input_queue.get_nowait()
        return line
    except queue.Empty:
        return None 