"""
Text Display Module
-----------------
Provides text display functionality for the assistant when speech isn't working.
This simply displays the speech text in the console.
"""

import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def speak(text):
    """
    Display speech text in the console
    
    Args:
        text (str): Text to display as speech
    """
    # Print the text to console with SPEECH tag
    print(f"[SPEECH]: {text}")
    
    # No sound, no waiting - just display the text
    # This makes sure the speech text is visible but doesn't delay execution
    
if __name__ == "__main__":
    # Test the text display
    speak("This is a test of the text display system.")
    speak("When you see [SPEECH], this is what the assistant would say if speech was working.") 