#!/usr/bin/env python
import os
import pyautogui
import psutil
import subprocess
import glob
import time
import threading
import logging
import random
from pathlib import Path
from ..modules.speech_utils import speak

# Configure logging
logger = logging.getLogger(__name__)

class MediaControls:
    """Class to handle media control operations"""
    
    def __init__(self):
        """Initialize MediaControls instance"""
        # Media control settings
        self.volume_step = 10  # Default volume step (percentage)
        
        # Media directories
        self.media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media')
        self.audio_dir = os.path.join(self.media_dir, 'audio')
        self.video_dir = os.path.join(self.media_dir, 'video')
        
        # Create directories if they don't exist
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        # Supported media file extensions
        self.audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
        self.video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
        
        # Default media players based on OS
        if os.name == 'nt':  # Windows
            self.default_audio_player = 'wmplayer.exe'
            self.default_video_player = 'wmplayer.exe'
            self.media_players = ['wmplayer.exe', 'vlc.exe', 'spotify.exe', 'musicapp.exe', 'groove.exe']
        else:  # Linux/Mac
            self.default_audio_player = 'vlc'
            self.default_video_player = 'vlc'
            self.media_players = ['vlc', 'rhythmbox', 'audacious', 'totem', 'mplayer']
        
        # Track current media state
        self.current_playlist = None
        self.media_process = None
        self.is_playing = False
        
    def _is_media_player_running(self):
        """Check if any known media player is running"""
        for proc in psutil.process_iter(['name']):
            try:
                process_name = proc.info['name'].lower()
                if any(player.lower() in process_name for player in self.media_players):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def _ensure_media_player(self):
        """Ensure a media player is running"""
        if not self._is_media_player_running():
            try:
                if os.name == 'nt':  # Windows
                    os.system(f"start {self.default_audio_player}")
                else:  # Linux/Mac
                    subprocess.Popen([self.default_audio_player], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                time.sleep(2)  # Wait for player to start
                return True
            except Exception as e:
                logger.error(f"Error launching media player: {e}")
                return False
        return True
    
    def process_media_command(self, command):
        """Process media control commands"""
        try:
            command = command.lower()
            
            # Ensure media player is running for media controls
            if not self._ensure_media_player():
                speak("Could not find or start a media player")
                return False
            
            # Play/Pause
            if command in ["play", "pause", "toggle"]:
                pyautogui.press("playpause")
                return True
                
            # Stop
            elif command == "stop":
                pyautogui.press("stop")
                self.is_playing = False
                return True
                
            # Next track
            elif command in ["next", "next track", "skip"]:
                pyautogui.press("nexttrack")
                return True
                
            # Previous track
            elif command in ["previous", "previous track", "back"]:
                pyautogui.press("prevtrack")
                return True
                
            # Volume controls
            elif "volume" in command:
                if "up" in command or "increase" in command:
                    pyautogui.press("volumeup", presses=2)
                    return True
                elif "down" in command or "decrease" in command:
                    pyautogui.press("volumedown", presses=2)
                    return True
                elif "mute" in command:
                    pyautogui.press("volumemute")
                    return True
            
            # Play specific media
            elif "play" in command:
                if "music" in command or "song" in command:
                    return self.play_audio()
                elif "video" in command:
                    return self.play_video()
                    
            # If command not recognized
            logger.warning(f"Unrecognized media command: {command}")
            return False
            
        except Exception as e:
            logger.error(f"Error processing media command: {e}")
            return False
    
    def play_audio(self, audio_name=None):
        """Play audio files from the audio directory"""
        try:
            if not os.path.exists(self.audio_dir):
                speak("No audio directory found")
                return False
            
            audio_files = []
            for ext in self.audio_extensions:
                audio_files.extend(glob.glob(os.path.join(self.audio_dir, f"*{ext}")))
            
            if not audio_files:
                speak("No audio files found")
                return False
            
            if audio_name:
                # Try to find a matching audio file
                audio_name = audio_name.lower()
                for file in audio_files:
                    if audio_name in os.path.basename(file).lower():
                        self._play_media(file, self.default_audio_player)
                        return True
                speak(f"Could not find audio file matching {audio_name}")
                return False
            else:
                # Play a random audio file
                audio_file = random.choice(audio_files)
                self._play_media(audio_file, self.default_audio_player)
                return True
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def play_video(self, video_name=None):
        """Play video files from the video directory"""
        try:
            if not os.path.exists(self.video_dir):
                speak("No video directory found")
                return False
            
            video_files = []
            for ext in self.video_extensions:
                video_files.extend(glob.glob(os.path.join(self.video_dir, f"*{ext}")))
            
            if not video_files:
                speak("No video files found")
                return False
            
            if video_name:
                # Try to find a matching video file
                video_name = video_name.lower()
                for file in video_files:
                    if video_name in os.path.basename(file).lower():
                        self._play_media(file, self.default_video_player)
                        return True
                speak(f"Could not find video file matching {video_name}")
                return False
            else:
                # Play a random video file
                video_file = random.choice(video_files)
                self._play_media(video_file, self.default_video_player)
                return True
                
        except Exception as e:
            logger.error(f"Error playing video: {e}")
            return False
    
    def _play_media(self, file_path, player):
        """Play media file using specified player"""
        try:
            if self.media_process:
                self.media_process.terminate()
                self.media_process = None
            
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.media_process = subprocess.Popen(
                    [player, file_path],
                    startupinfo=startupinfo,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:  # Linux/Mac
                self.media_process = subprocess.Popen(
                    [player, file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            self.is_playing = True
            return True
            
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            return False
    
    def cleanup(self):
        """Clean up media processes"""
        if self.media_process:
            try:
                self.media_process.terminate()
                self.media_process = None
            except:
                pass
        self.is_playing = False

    def adjust_volume(self, direction):
        """Adjust system volume up or down"""
        try:
            if direction == "up":
                pyautogui.press("volumeup", presses=2)
            elif direction == "down":
                pyautogui.press("volumedown", presses=2)
            return True
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return False
            
    def mute_volume(self):
        """Mute/unmute system volume"""
        try:
            pyautogui.press("volumemute")
            return True
        except Exception as e:
            logger.error(f"Error muting volume: {e}")
            return False 