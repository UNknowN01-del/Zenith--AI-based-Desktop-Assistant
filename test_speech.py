#!/usr/bin/env python
"""
Text-to-Speech Test Script
-------------------------
This script tests different text-to-speech backends to identify which ones work
on your system. It's useful for troubleshooting speech issues with the AI Assistant.
"""

import sys
import os
import logging
import platform
import time

print("======= Text-to-Speech Diagnostic Tool =======")
print(f"Operating System: {platform.system()} {platform.release()}")
print(f"Python Version: {sys.version.split()[0]}")
print("=============================================\n")

# Test pyttsx3 (the default engine)
print("Testing pyttsx3 engine...")
try:
    import pyttsx3
    
    # List all available voices
    print("Available voices in pyttsx3:")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for idx, voice in enumerate(voices):
        print(f"  {idx + 1}. {voice.name}")
        print(f"     ID: {voice.id}")
    
    # Try to speak
    print("\nTrying to speak with pyttsx3...")
    engine.setProperty('rate', 150)
    
    # Try first voice
    if voices:
        print(f"Using voice: {voices[0].name}")
        engine.setProperty('voice', voices[0].id)
    
    engine.say("This is a test of the pyttsx3 text to speech engine.")
    engine.runAndWait()
    print("✅ pyttsx3 test completed. Did you hear anything?")
    
except Exception as e:
    print(f"❌ Error with pyttsx3: {e}")

# Test alternative TTS methods if pyttsx3 fails
print("\nTesting alternative TTS methods...")

# Try Windows SAPI directly (Windows only)
if platform.system() == 'Windows':
    print("\nTesting Windows SAPI directly...")
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # List available voices
        print("Available voices in SAPI:")
        voices = speaker.GetVoices()
        for i in range(voices.Count):
            voice = voices.Item(i)
            print(f"  {i + 1}. {voice.GetDescription()}")
        
        # Try to speak
        print("\nTrying to speak with SAPI...")
        speaker.Speak("This is a test of the Windows Speech API.")
        print("✅ Windows SAPI test completed. Did you hear anything?")
        
    except Exception as e:
        print(f"❌ Error with Windows SAPI: {e}")

# Try pygame for audio playback (cross-platform)
print("\nTesting pygame for TTS audio playback...")
try:
    import pygame
    pygame.init()
    pygame.mixer.init()
    print("✅ pygame initialized successfully. This could be used as an alternative audio backend.")
except Exception as e:
    print(f"❌ Error initializing pygame: {e}")

print("\n=============== Recommendations ===============")
print("If pyttsx3 is not working:")
print("1. Check your audio device settings - make sure speakers are connected and volume is up")
print("2. Try running the AI Assistant with administrator privileges")
print("3. Check Windows Speech settings (Windows only):")
print("   - Open Windows Settings > Time & Language > Speech")
print("   - Make sure speech services are enabled")
print("4. Try installing additional voices:")
print("   - On Windows: Control Panel > Speech > Text to Speech")
print("   - Add new voices through Windows Settings")
print("5. Try using a different TTS engine - see documentation for alternatives")
print("\nTo use this diagnosis in your AI Assistant:")
print("1. Open 'assistant/modules/speech_utils.py'")
print("2. If pyttsx3 is failing but SAPI works directly, modify the code to use the SAPI method")

# Additional info
print("\n============== System Details ===============")
import subprocess

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

# Check audio devices
if platform.system() == 'Windows':
    print("\nAudio Devices (Windows):")
    print(run_cmd("powershell -Command \"Get-WmiObject Win32_SoundDevice | Select Name, Status | Format-Table -AutoSize\""))
elif platform.system() == 'Linux':
    print("\nAudio Devices (Linux):")
    print(run_cmd("aplay -l"))
elif platform.system() == 'Darwin':  # macOS
    print("\nAudio Devices (macOS):")
    print(run_cmd("system_profiler SPAudioDataType | grep -A 3 'Output'"))

print("\n============================================")
print("Diagnostic complete. Use this information to troubleshoot your TTS issues.")
print("If you need help, check the documentation or report the issue with these diagnostics.") 