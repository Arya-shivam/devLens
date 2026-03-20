import sys
import re

def is_piped() -> bool:
    """Check if data is being piped into stdin."""
    return not sys.stdin.isatty()

def read_stdin() -> str:
    """Read all data from stdin."""
    return sys.stdin.read()

def parse_error(traceback_text: str) -> str:
    """
    Extract the actual error message or last significant line from a stack trace.
    This strips out local file paths and line numbers to preserve privacy.
    """
    lines = [L.strip() for L in traceback_text.splitlines() if L.strip()]
    if not lines:
        return ""
        
    error_line = lines[-1]
    
    # Simple regex to extract ErrorType: Message
    match = re.search(r'([A-Za-z0-9_]+Error.*)', error_line)
    if match:
        return match.group(1)
        
    if "Exception" in error_line:
        match = re.search(r'([A-Za-z0-9_]*Exception.*)', error_line)
        if match:
            return match.group(1)
            
    # if no matching Error/Exception class, just return the last line
    return error_line
