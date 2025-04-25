#!/usr/bin/env python
import speech_recognition as sr
import pyttsx3
import logging
import os
from google.cloud import texttospeech
from pathlib import Path
import time
import threading

# Set up logging to show only important information
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simplified format
    handlers=[
        logging.FileHandler('assistant.log'),  # Full logs in file
        logging.StreamHandler()  # Simplified logs in console
    ]
)
logger = logging.getLogger(__name__)

# Disable debug logs from other libraries
logging.getLogger('comtypes').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Voice settings
VOICE_TYPE = "local"  # Can be "local" or "google"
GOOGLE_VOICE_NAME = "en-IN-Standard-A"  # Indian English female voice
GOOGLE_VOICE_GENDER = texttospeech.SsmlVoiceGender.FEMALE

# Global engine instance
_engine = None
_speech_lock = threading.Lock()

def initialize_speech_engine():
    """Initialize the speech engine."""
    global _engine
    try:
        _engine = pyttsx3.init()
        # Set properties
        _engine.setProperty('rate', 150)  # Speed of speech
        
        # Get available voices
        voices = _engine.getProperty('voices')
        
        # Try to find an Indian English voice
        indian_voice = None
        for voice in voices:
            if "indian" in voice.name.lower() or "hindi" in voice.name.lower():
                indian_voice = voice.id
                break
                
        # If Indian voice found, set it
        if indian_voice:
            _engine.setProperty('voice', indian_voice)
        # Otherwise use the first voice
        elif voices:
            _engine.setProperty('voice', voices[0].id)
            
        return True
    except Exception as e:
        logger.error(f"Error initializing speech engine: {e}")
        return False

def recognize_speech():
    """Captures voice command and converts it to text"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("\nListening...")
            
            # Make it more sensitive to speech
            recognizer.energy_threshold = 250  # Lower threshold for softer speech
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.6  # Slightly longer pause for Indian English rhythm
            recognizer.operation_timeout = None
            
            # Shorter duration for ambient noise adjustment
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Ready to listen.")
            
            try:
                audio = recognizer.listen(source)
                print("Processing speech...")

                try:
                    # Using en-IN for Indian English
                    text = recognizer.recognize_google(
                        audio,
                        language="en-IN",  # Indian English
                        show_all=False  # Only return most confident result
                    )
                    print(f"You said: {text}")
                    return text.lower()
                except sr.UnknownValueError:
                    print("Sorry, I couldn't understand what you said.")
                    return None
                except sr.RequestError as e:
                    print("Could not request results from speech service.")
                    return None
            except Exception as e:
                print("Error during listening. Please try again.")
                return None
                
    except Exception as e:
        print("Error accessing microphone. Please check your microphone settings.")
        return None

def speak_google(text):
    """Converts text to speech using Google Cloud TTS"""
    try:
        # Initialize the client
        client = texttospeech.TextToSpeechClient()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-IN",
            name=GOOGLE_VOICE_NAME,
            ssml_gender=GOOGLE_VOICE_GENDER
        )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Create output directory if it doesn't exist
        output_dir = Path("temp_audio")
        output_dir.mkdir(exist_ok=True)
        
        # Save the audio file
        output_file = output_dir / "output.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
            
        # Play the audio file using system default player
        os.system(f'start {output_file}')
        
    except Exception as e:
        print(f"Error with Google TTS: {e}")
        # Fallback to local TTS
        speak_local(text)

def speak_local(text):
    """Converts text to speech using local Windows TTS"""
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # Adjust speed
    
    # Get available voices
    voices = engine.getProperty('voices')
    
    # Try to find an Indian English voice
    indian_voice_found = False
    for voice in voices:
        if "indian" in voice.name.lower() or "en-in" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            indian_voice_found = True
            break
    
    if not indian_voice_found:
        print("No Indian English voice found, using default voice")
    
    engine.say(text)
    engine.runAndWait()

def speak(text):
    """
    Convert text to speech
    
    Args:
        text (str): Text to convert to speech
    """
    global _engine, _speech_lock
    
    # Initialize engine if not already done
    if _engine is None:
        if not initialize_speech_engine():
            print(f"[SPEECH]: {text}")
            return
    
    try:
        with _speech_lock:
            # Print the text to console as well
            print(f"[SPEECH]: {text}")
            
            # Check if engine is busy
            if _engine._inLoop:
                # Stop the current speech if it's running
                _engine.stop()
                time.sleep(0.1)  # Give a small delay
            
            # Say the text
            _engine.say(text)
            _engine.runAndWait()
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        print(f"[SPEECH ERROR]: {text}")

def list_available_voices():
    """Lists all available voices (both local and Google Cloud)"""
    print("\nLocal Windows Voices:")
    print("===================")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for idx, voice in enumerate(voices):
        print(f"{idx + 1}. {voice.name}")
        print(f"   ID: {voice.id}")
        print("-------------------")
    
    print("\nGoogle Cloud Voices (Indian English):")
    print("=================================")
    try:
        client = texttospeech.TextToSpeechClient()
        voices = client.list_voices(language_code="en-IN")
        for idx, voice in enumerate(voices.voices):
            print(f"{idx + 1}. {voice.name}")
            print(f"   Gender: {voice.ssml_gender}")
            print("-------------------")
    except Exception as e:
        print("Error accessing Google Cloud voices. Make sure you have set up Google Cloud credentials.")

# Initialize the speech engine when module is imported
initialize_speech_engine()
