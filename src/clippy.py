import pyperclip

def read_clipboard():
    """Reads and returns the current content of the system clipboard."""
    try:
        return pyperclip.paste()
    except pyperclip.PyperclipException as e:
        print(f"Error accessing clipboard: {e}")
        # Depending on requirements, you might want to return None, an empty string,
        # or raise the exception.
        return None
    except Exception as e: # Catch potential import errors if pyperclip isn't installed
         print(f"Error: pyperclip library might not be installed or accessible. {e}")
         return None
