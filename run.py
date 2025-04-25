#!/usr/bin/env python
"""
AI Desktop Assistant
-------------------
Main executable file for the AI Desktop Assistant project.

This script initializes the assistant and starts the main command loop.
It handles speech recognition, command processing, and manages system features.

Author: Aman
License: MIT
"""

import sys
import os
import logging
import time
import keyboard
import threading
import platform
import webbrowser
import re
from assistant.modules.nlp_learning import CommandLearner
from assistant.modules.speech_recognition_engine import SpeechRecognizer
from assistant.modules.ai_orchestrator import AIOrchestrator
from assistant.modules.speech_utils import speak
from assistant.modules.system_controls import SystemControls
from assistant.modules.media_controls import MediaControls
from assistant.modules.web_search import WebSearch
from assistant.modules.config_handler import config
from assistant.gui import create_gui

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("assistant.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global instances
gui = None
web_search = None

def custom_speak(text):
    """Wrapper for speak function that updates GUI"""
    if gui:
        gui.speak(text, is_user=False)
    speak(text)

def check_environment():
    """Check if all required components are available"""
    try:
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            logger.error("Python 3.8 or higher is required")
            return False
            
        # Check if running in virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.warning("Not running in a virtual environment. It's recommended to use a virtual environment.")
        
        # Check required directories
        required_dirs = ['training_data', 'models', 'screenshots']
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
        
        # Check for config file
        if not os.path.exists('config.json'):
            logger.error("config.json not found")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Environment check failed: {e}")
        return False

def split_compound_commands(command_text):
    """
    Split compound commands into individual commands.
    
    Args:
        command_text (str): The full command text that may contain multiple commands
        
    Returns:
        list: List of individual commands
    """
    # Common conjunctions and delimiters that separate commands
    conjunctions = [
        r'\band\b',  # Match "and" as a whole word
        r'\bthen\b',  # Match "then" as a whole word
        r'\balso\b',  # Match "also" as a whole word
        r';'          # Semicolon as a command separator
    ]
    
    # Create a pattern that matches any of the conjunctions
    pattern = '|'.join(conjunctions)
    
    # Split the command text
    commands = re.split(pattern, command_text, flags=re.IGNORECASE)
    
    # Clean up each command (remove leading/trailing whitespace)
    commands = [cmd.strip() for cmd in commands if cmd.strip()]
    
    logger.info(f"Split compound command into: {commands}")
    return commands

def process_command(command_text):
    """Process a voice command"""
    try:
        # Check for exact quit commands
        if command_text.strip().lower() in ["quit zenith", "quit ai", "exit ai"]:
            custom_speak("Goodbye! Shutting down.")
            os._exit(0)  # Use os._exit(0) to ensure the program exits
        
        # Split into individual commands if it's a compound command
        individual_commands = split_compound_commands(command_text)
        
        # If multiple commands were detected
        if len(individual_commands) > 1:
            custom_speak(f"Processing {len(individual_commands)} commands")
            
            # Process each command sequentially
            for i, cmd in enumerate(individual_commands):
                logger.info(f"Processing command {i+1}/{len(individual_commands)}: {cmd}")
                
                # Process this individual command
                result = orchestrator.preprocess_command(cmd)
                command = result.get("command", "")
                category = result.get("category", "web_search")
                confidence = result.get("confidence", 0.0)
                
                logger.info(f"Command {i+1} category: {category}, confidence: {confidence}")
                
                # Handle lock computer command directly with high confidence
                if any(phrase in command.lower() for phrase in ["lock computer", "lock system", "lock pc"]):
                    custom_speak("Locking your computer.")
                    sys_controls.system_power_control(command)
                    break  # Exit after locking
                
                # Only process commands with sufficient confidence
                if confidence < 0.4:
                    logger.warning(f"Low confidence ({confidence}) for command {i+1}: {command}")
                    custom_speak(f"I'm not sure what you want me to do with '{cmd}'. Skipping this part.")
                    continue
                
                # Process the command with appropriate handlers
                process_single_command(command, category, confidence)
                
            return
        
        # If it's just a single command, process it normally
        result = orchestrator.preprocess_command(command_text)
        command = result.get("command", "")
        category = result.get("category", "web_search")
        confidence = result.get("confidence", 0.0)
        
        logger.info(f"Command category: {category}, confidence: {confidence}")
        
        # Handle lock computer command directly with high confidence
        if any(phrase in command.lower() for phrase in ["lock computer", "lock system", "lock pc"]):
            custom_speak("Locking your computer.")
            sys_controls.system_power_control(command)
            return
            
        # Only process commands with sufficient confidence
        if confidence < 0.4:
            logger.warning(f"Low confidence ({confidence}) for command: {command}")
            custom_speak("I'm not sure what you want me to do. Could you please rephrase that?")
            return
            
        # Process the command with appropriate handlers
        process_single_command(command, category, confidence)
            
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        custom_speak("Sorry, I encountered an error while processing your command")

def process_single_command(command, category, confidence):
    """Process a single command with determined category"""
    try:
        # Enhance YouTube command recognition
        if "youtube" in command.lower():
            if "search" in command.lower():
                category = "youtube_search"
            elif "play" in command.lower():
                category = "youtube_play"
        
        # Handle different command categories
        if category == "youtube_search":
            # Only search YouTube without playing
            search_query = command.lower().replace("search", "").replace("youtube", "").replace("for", "").replace("on", "").strip()
            custom_speak(f"Searching YouTube for {search_query}")
            web_search.search_youtube(search_query)
            
        elif category == "youtube_play":
            # Search and play the first video
            search_query = command.lower().replace("play", "").replace("youtube", "").replace("on", "").strip()
            custom_speak(f"Playing {search_query} on YouTube")
            web_search.play_youtube_video(search_query)
                
        elif category == "screenshot":
            custom_speak("Taking a screenshot")
            sys_controls.take_screenshot()
            
        elif category == "system_control":
            handle_system_command(command)
            
        elif category == "media_control":
            handle_media_command(command)
            
        elif category == "system_info":
            handle_system_info_command(command)
            
        elif category == "video_control":
            # For generic video commands, default to YouTube search without playing
            if "youtube" in command.lower():
                search_query = command.lower().replace("video", "").replace("youtube", "").replace("on", "").strip()
                custom_speak(f"Searching YouTube for {search_query}")
                web_search.search_youtube(search_query)
            else:
                handle_media_command(command)
            
        else:  # Default to web search
            custom_speak(f"Searching the web for {command}")
            web_search.search_web(command)
    
    except Exception as e:
        logger.error(f"Error processing single command: {e}")
        custom_speak("Sorry, I encountered an error processing that part of your command")

def handle_system_command(command):
    """
    Handle system control commands such as opening applications, adjusting volume, etc.

    Args:
        command (str): The command to process

    Returns:
        None
    """
    try:
        command = command.lower()
        
        # Window control commands (minimize, maximize, restore)
        if any(word in command for word in ["minimize", "maximise", "maximize", "restore"]):
            result = sys_controls.control_window(command)
            if not result:
                custom_speak("I couldn't control the window. Please try again.")
            return
            
        # Volume control commands
        elif "volume" in command:
            result = sys_controls.adjust_volume(command)
            if not result:
                custom_speak("I couldn't adjust the volume. Please try again.")
            return
            
        # Brightness control commands
        elif "brightness" in command:
            result = sys_controls.adjust_brightness(command)
            if not result:
                custom_speak("I couldn't adjust the brightness. Please try again.")
            return
            
        # Application launch commands
        elif any(word in command for word in ["open", "launch", "start", "run"]):
            result = sys_controls.launch_application(command)
            if not result:
                custom_speak("I couldn't launch the application. Please try again.")
            return
            
        # System power commands
        elif any(word in command for word in ["shutdown", "restart", "reboot", "log off", "sign out", "lock"]):
            result = sys_controls.system_power_control(command)
            if not result:
                custom_speak("I couldn't perform the system power operation. Please try again.")
            return
            
        # If none of the above matched, try the general control_system method
        result = sys_controls.control_system(command)
        if not result:
            custom_speak("I couldn't process your system command. Please try again.")
            
    except Exception as e:
        logger.error(f"Error handling system command: {str(e)}")
        custom_speak("Sorry, I encountered an error while processing the system command.")

def handle_system_info_command(command):
    """
    Handle system information commands such as time, date, battery, etc.

    Args:
        command (str): The command to process

    Returns:
        None
    """
    try:
        command = command.lower()
        
        # Time and date commands
        if "time" in command or "date" in command:
            sys_controls.get_date_time(command)
            return
            
        # Battery commands
        elif any(word in command for word in ["battery", "charge", "power"]):
            # Get battery info and ensure it speaks the result
            result = sys_controls.get_battery_info()
            if not result:
                custom_speak("I couldn't retrieve battery information")
            return
            
        # WiFi commands
        elif any(word in command for word in ["wifi", "network", "internet", "connection"]):
            result = sys_controls.get_wifi_info()
            if not result:
                custom_speak("I couldn't retrieve WiFi information")
            return
            
        # CPU, memory, disk commands
        elif any(word in command for word in ["cpu", "processor", "memory", "ram", "disk", "storage", "drive"]):
            result = sys_controls.get_system_info(command)
            if not result:
                custom_speak("I couldn't retrieve system information")
            return
            
        # Temperature commands
        elif any(word in command for word in ["temperature", "temp", "hot"]):
            result = sys_controls.get_temperature()
            if not result:
                custom_speak("I couldn't retrieve temperature information")
            return
            
        # General system info command
        else:
            result = sys_controls.get_system_info(command)
            if not result:
                custom_speak("I couldn't retrieve system information")
            
    except Exception as e:
        logger.error(f"Error handling system info command: {str(e)}")
        custom_speak("Sorry, I encountered an error while retrieving system information.")

def handle_media_command(command):
    """
    Handle media control commands such as play, pause, next, previous, etc.

    Args:
        command (str): The command to process

    Returns:
        None
    """
    try:
        command = command.lower()
        
        # Basic media playback controls
        if any(word in command for word in ["play", "pause", "stop", "resume"]):
            action = next(word for word in ["play", "pause", "stop", "resume"] if word in command)
            custom_speak(f"{action.capitalize()}ing media")
            media_controls.process_media_command(action)
            return
            
        # Track navigation
        elif any(word in command for word in ["next", "previous", "skip"]):
            if "next" in command or "skip" in command:
                custom_speak("Playing next track")
                media_controls.process_media_command("next")
            else:
                custom_speak("Playing previous track")
                media_controls.process_media_command("previous")
            return
            
        # Volume control (this might overlap with system controls)
        elif any(word in command for word in ["volume", "louder", "quieter"]):
            if any(word in command for word in ["up", "increase", "louder"]):
                custom_speak("Increasing volume")
                media_controls.process_media_command("volume_up")
            elif any(word in command for word in ["down", "decrease", "quieter"]):
                custom_speak("Decreasing volume")
                media_controls.process_media_command("volume_down")
            elif "mute" in command:
                custom_speak("Muting media")
                media_controls.process_media_command("mute")
            return
            
        # If none of the above matched, try the general process_media_command
        result = media_controls.process_media_command(command)
        if not result:
            custom_speak("I couldn't process your media command. Please try again.")
            
    except Exception as e:
        logger.error(f"Error handling media command: {str(e)}")
        custom_speak("Sorry, I encountered an error while processing the media command.")

class KeyboardController:
    """Handles keyboard events and hotkey management"""
    
    def __init__(self):
        """Initialize KeyboardController instance"""
        self.listening = False
        self.speech_recognizer = SpeechRecognizer()
        # Set up P key events
        keyboard.on_press_key('p', self.start_listening)
        keyboard.on_release_key('p', self.stop_listening)
        print("\nSpeech recognition initialized. Hold 'P' to speak...")
    
    def start_listening(self, e):
        """Start listening for voice commands when P is pressed"""
        if not self.listening:
            self.listening = True
            print("\n🎤 Listening... (Hold P and speak)")
            threading.Thread(target=self._listen_thread, daemon=True).start()
    
    def stop_listening(self, e):
        """Stop listening for voice commands when P is released"""
        if self.listening:
            self.listening = False
            print("\n🛑 Stopped listening.")
    
    def _listen_thread(self):
        """Background thread for voice recognition"""
        try:
            # Use a shorter timeout since we're using hold-to-talk
            recognized_text = self.speech_recognizer.listen(timeout=3)
            
            if recognized_text and len(recognized_text.strip()) > 0:
                print(f"\n🎯 Recognized: {recognized_text}")
                process_command(recognized_text)
            else:
                print("\n❌ No speech detected. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in listening thread: {e}")
            print("\n⚠️ Error processing speech. Please try again.")
        finally:
            self.listening = False

def main():
    """Main function to run the assistant"""
    global gui, orchestrator, sys_controls, media_controls, web_search
    
    # Initialize GUI
    gui = create_gui()
    
    # Initialize components
    orchestrator = AIOrchestrator()
    sys_controls = SystemControls()
    media_controls = MediaControls()
    web_search = WebSearch()
    
    # Check environment
    if not check_environment():
        custom_speak("Environment check failed. Please check the logs.")
        sys.exit(1)
    
    # Initialize speech recognizer
    recognizer = SpeechRecognizer()
    
    # Introduce the AI
    print("Hello! I'm Zenith, your AI assistant. I can help you with various tasks like checking the weather, playing music, and more. Just ask!")
    speak("Hello! I'm Zenith, your AI assistant. I can help you with various tasks like checking the weather, playing music, and more. Just ask!")
    
    def listen_callback():
        """Callback for the Listen button"""
        try:
            command = recognizer.listen()
            if command:
                process_command(command)
        except Exception as e:
            logger.error(f"Error in listen callback: {e}")
            custom_speak("Sorry, I encountered an error while processing your command.")
    
    def stop_callback(silent=False):
        """Callback for the Stop button"""
        try:
            # Add any cleanup code here
            if not silent:
                custom_speak("Stopping current operation")
        except Exception as e:
            logger.error(f"Error in stop callback: {e}")
    
    # Set up GUI callbacks
    gui.set_speak_command(listen_callback)
    gui.set_stop_command(stop_callback)
    
    # Welcome message
    custom_speak("AI Desktop Assistant is ready!")
    
    # Start GUI main loop
    gui.root.mainloop()

if __name__ == "__main__":
    main()
