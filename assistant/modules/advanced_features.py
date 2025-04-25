#!/usr/bin/env python
import os
import pyautogui
import psutil
import requests
import random
import subprocess
import glob
import time
import threading
from datetime import datetime
from ..modules.speech_utils import speak
from ..modules.web_search import search_web
import re
import platform
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import ImageGrab, Image

# Configure logging
logger = logging.getLogger(__name__)

class AdvancedFeatures:
    def __init__(self):
        # Create base directories
        self.screenshot_dir = "screenshots"
        self.media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media')
        self.audio_dir = os.path.join(self.media_dir, 'audio')
        self.video_dir = os.path.join(self.media_dir, 'video')
        
        # Create directories if they don't exist
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        # Supported media file extensions
        self.audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
        self.video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
        
        # Default media players based on OS
        if os.name == 'nt':  # Windows
            self.default_audio_player = 'wmplayer.exe'
            self.default_video_player = 'wmplayer.exe'
            self.media_players = ['wmplayer.exe', 'vlc.exe', 'spotify.exe', 'musicapp.exe', 'groove.exe', 'movies.exe', 'video.exe']
        else:  # Linux/Mac
            self.default_audio_player = 'vlc'
            self.default_video_player = 'vlc'
            self.media_players = ['vlc', 'rhythmbox', 'audacious', 'totem', 'mplayer', 'mpv']
        
        # Track current playlist and media process
        self.current_playlist_path = None
        self.media_process = None
        self.media_thread = None
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
    
    def _ensure_media_player_running(self):
        """Ensure a media player is running, launch one if needed"""
        if not self._is_media_player_running():
            speak("No media player detected. Launching default media player.")
            try:
                if os.name == 'nt':  # Windows
                    os.system(f"start {self.default_audio_player}")
                else:  # Linux/Mac
                    subprocess.Popen([self.default_audio_player], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                return True
            except Exception as e:
                print(f"Error launching media player: {e}")
                return False
        return True
    
    def _is_windows_media_player_running(self):
        """Check if Windows Media Player is running"""
        if os.name != 'nt':  # Only for Windows
            return False
            
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == 'wmplayer.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def _focus_media_player(self):
        """Focus the media player window to ensure commands are received"""
        try:
            if os.name == 'nt':  # Windows
                # Try to focus Windows Media Player
                if self._is_windows_media_player_running():
                    # Use Windows API to find and focus the window
                    try:
                        import win32gui
                        import win32con
                        
                        def callback(hwnd, windows):
                            if win32gui.IsWindowVisible(hwnd) and "Windows Media Player" in win32gui.GetWindowText(hwnd):
                                windows.append(hwnd)
                            return True
                        
                        windows = []
                        win32gui.EnumWindows(callback, windows)
                        
                        if windows:
                            # Focus the first found window
                            win32gui.ShowWindow(windows[0], win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(windows[0])
                            return True
                    except ImportError:
                        # If win32gui is not available, try alternative method
                        os.system("taskkill /f /im wmplayer.exe")
                        time.sleep(0.5)
                        os.system("start wmplayer")
                        time.sleep(2)  # Wait for it to start
                        return True
            
            # For other OS or if Windows-specific method failed
            return False
        except Exception as e:
            print(f"Error focusing media player: {e}")
            return False
    
    def _is_vlc_player_running(self):
        """Check if VLC Player is running"""
        for proc in psutil.process_iter(['name']):
            try:
                process_name = proc.info['name'].lower()
                if 'vlc' in process_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def _create_vlc_playlist(self, directory, file_extensions, random_selection=False, max_items=10):
        """Create a VLC playlist with all media files in the directory or a random selection
        
        Args:
            directory: Directory containing media files
            file_extensions: List of file extensions to include
            random_selection: If True, select random files instead of all files
            max_items: Maximum number of items to include if random_selection is True
            
        Returns:
            Path to the created playlist or None if failed
        """
        try:
            # Get all media files with absolute paths
            media_files = []
            for ext in file_extensions:
                found_files = glob.glob(os.path.join(directory, f"*{ext}"))
                # Convert to absolute paths
                found_files = [os.path.abspath(f) for f in found_files]
                media_files.extend(found_files)
            
            if not media_files:
                print("No media files found in directory:", directory)
                return None
            
            # Print found files for debugging
            print(f"Found {len(media_files)} media files in {directory}:")
            for file in media_files[:5]:  # Print first 5 files
                print(f"  - {os.path.basename(file)}")
            if len(media_files) > 5:
                print(f"  ... and {len(media_files) - 5} more")
            
            # If random selection is requested and we have enough files
            if random_selection and len(media_files) > max_items:
                print(f"Selecting {max_items} random media files for playlist")
                media_files = random.sample(media_files, max_items)
            else:
                print(f"Adding all {len(media_files)} media files to playlist")
                
            # If there's only one file, duplicate it to ensure playlist navigation works
            if len(media_files) == 1:
                print(f"Only one media file found in {directory}. Next/previous track commands may not work as expected.")
                # Duplicate the file in the playlist to make next/previous work
                media_files = [media_files[0]] * 3  # Add the same file multiple times
                
            # Create a temporary playlist file with absolute path
            playlist_path = os.path.join(directory, "playlist.m3u")
            playlist_path = os.path.abspath(playlist_path)
            
            print(f"Creating playlist at: {playlist_path}")
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for file_path in media_files:
                    # Use absolute paths for better compatibility
                    f.write(f"{file_path}\n")
            
            # Verify playlist was created
            if os.path.exists(playlist_path):
                print(f"Playlist created successfully with {len(media_files)} entries")
                # Store the playlist path for cleanup later
                self.current_playlist_path = playlist_path
                return playlist_path
            else:
                print("Failed to create playlist file")
                return None
                
        except Exception as e:
            print(f"Error creating VLC playlist: {e}")
            return None
    
    def _cleanup_playlist(self):
        """Remove the temporary playlist file when exiting"""
        try:
            if hasattr(self, 'current_playlist_path') and self.current_playlist_path:
                if os.path.exists(self.current_playlist_path):
                    os.remove(self.current_playlist_path)
                    print(f"Removed temporary playlist: {self.current_playlist_path}")
                    self.current_playlist_path = None
        except Exception as e:
            print(f"Error cleaning up playlist: {e}")
    
    def _play_media_in_thread(self, file_path, player):
        """Play media in a separate thread"""
        try:
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self.media_process = subprocess.Popen(
                    [player, file_path],
                    startupinfo=startupinfo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:  # Linux/Mac
                self.media_process = subprocess.Popen(
                    [player, file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            self.is_playing = True
            self.media_process.wait()
            self.is_playing = False
        except Exception as e:
            print(f"Error playing media: {e}")
            self.is_playing = False

    def _open_media_file(self, file_path, default_player):
        """Open media file in a non-blocking way"""
        try:
            # Stop any currently playing media
            self.stop_media()
            
            # Start new media playback in a thread
            self.media_thread = threading.Thread(
                target=self._play_media_in_thread,
                args=(file_path, default_player)
            )
            self.media_thread.daemon = True  # Thread will be terminated when main program exits
            self.media_thread.start()
            return True
        except Exception as e:
            print(f"Error opening media file: {e}")
            return False

    def stop_media(self):
        """Stop currently playing media"""
        try:
            if self.media_process and self.is_playing:
                self.media_process.terminate()
                self.is_playing = False
                time.sleep(0.5)  # Give some time for the process to terminate
            return True
        except Exception as e:
            print(f"Error stopping media: {e}")
            return False

    def handle_media(self, command):
        """Handle media control commands including brightness and volume"""
        try:
            # Extract volume level if specified
            volume_level = None
            volume_match = re.search(r'(\d+)(?:\s+)?(%|percent)', command)
            if volume_match:
                volume_level = int(volume_match.group(1))
            
            # Extract brightness level if specified
            brightness_level = None
            brightness_match = re.search(r'(\d+)(?:\s+)?(%|percent)', command)
            if brightness_match and any(word in command.lower() for word in ["brightness", "screen", "display"]):
                brightness_level = int(brightness_match.group(1))
            
            # Handle brightness control directly through system
            if any(word in command.lower() for word in ["brightness", "screen brightness", "dim", "brighten"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                if "up" in command.lower() or "increase" in command.lower() or any(word in command.lower() for word in ["higher", "brighter"]):
                    print("Executing: Increase brightness")
                    self._adjust_brightness(10)  # Increase by 10%
                    return True
                elif "down" in command.lower() or "decrease" in command.lower() or any(word in command.lower() for word in ["lower", "dimmer"]):
                    print("Executing: Decrease brightness")
                    self._adjust_brightness(-10)  # Decrease by 10%
                    return True
                elif "set" in command.lower() and brightness_level is not None:
                    print(f"Executing: Set brightness to {brightness_level}%")
                    self._set_brightness(brightness_level)
                    return True
                elif "max" in command.lower() or "maximum" in command.lower() or "full" in command.lower():
                    print("Executing: Set brightness to maximum (100%)")
                    self._set_brightness(100)
                    return True
                elif "min" in command.lower() or "minimum" in command.lower():
                    print("Executing: Set brightness to minimum (10%)")
                    self._set_brightness(10)  # Not 0 to avoid complete darkness
                    return True
            
            # Handle volume controls directly through system
            if any(word in command.lower() for word in ["volume", "audio", "sound", "louder", "quieter"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                if ("up" in command.lower() or "increase" in command.lower() or "louder" in command.lower() or "higher" in command.lower()) and volume_level is None:
                    print("Executing: Increase volume")
                    # Use system volume keys directly
                    for _ in range(5):
                        pyautogui.press('volumeup')
                        time.sleep(0.1)  # Small delay between presses
                    return True
                elif ("down" in command.lower() or "decrease" in command.lower() or "quieter" in command.lower() or "lower" in command.lower()) and volume_level is None:
                    print("Executing: Decrease volume")
                    # Use system volume keys directly
                    for _ in range(5):
                        pyautogui.press('volumedown')
                        time.sleep(0.1)  # Small delay between presses
                    return True
                elif "set" in command.lower() and volume_level is not None:
                    print(f"Executing: Set volume to {volume_level}%")
                    self._set_volume(volume_level)
                    return True
                elif "max" in command.lower() or "maximum" in command.lower() or "full" in command.lower():
                    print("Executing: Set volume to maximum (100%)")
                    self._set_volume(100)
                    return True
                elif "min" in command.lower() or "minimum" in command.lower():
                    print("Executing: Set volume to minimum (10%)")
                    self._set_volume(10)  # Not 0 to avoid complete silence
                    return True
                elif "mute" in command.lower():
                    print("Executing: Mute volume")
                    pyautogui.press('volumemute')
                    return True
                elif "unmute" in command.lower():
                    print("Executing: Unmute volume")
                    pyautogui.press('volumemute')
                    return True
                
            # If we get here, this might be a media player command, check if we need to handle it
            if any(word in command.lower() for word in ["pause", "play", "stop", "next", "previous"]):
                print(f"Command: {command} | Category: media_control | Confidence: 0.9")
                # Check if a media player is running before trying to control it
                is_media_player_running = self._is_windows_media_player_running() or self._is_vlc_player_running()
                
                if is_media_player_running:
                    # Try to focus the media player window
                    self._focus_media_player()
                    
                    if "pause" in command.lower() or "stop" in command.lower():
                        print("Executing: Pause media")
                        # Use space key for most media players
                        pyautogui.press('space')
                        return True
                    elif "play" in command.lower() and not any(word in command.lower() for word in ["music", "song", "video", "movie", "audio"]):
                        print("Executing: Play media")
                        # Use space key for most media players
                        pyautogui.press('space')
                        return True
                    elif "next" in command.lower() or "skip" in command.lower():
                        print("Executing: Next track")
                        # Try next track key
                        pyautogui.press('nexttrack')
                        return True
                    elif "previous" in command.lower() or "back" in command.lower():
                        print("Executing: Previous track")
                        # Try previous track key
                        pyautogui.press('prevtrack')
                        return True
                else:
                    # No media player is running, use generic media keys
                    if "pause" in command.lower() or "stop" in command.lower():
                        print("Executing: Pause media (system key)")
                        pyautogui.press('playpause')
                        return True
                    elif "play" in command.lower():
                        print("Executing: Play media (system key)")
                        pyautogui.press('playpause')
                        return True
                    elif "next" in command.lower() or "skip" in command.lower():
                        print("Executing: Next track (system key)")
                        pyautogui.press('nexttrack')
                        return True
                    elif "previous" in command.lower() or "back" in command.lower():
                        print("Executing: Previous track (system key)")
                        pyautogui.press('prevtrack')
                        return True
            
            return False
                
        except Exception as e:
            print(f"Error handling media controls: {e}")
            return False
    
    def _set_volume(self, volume_level):
        """Set system volume to a specific level (0-100)"""
        try:
            print(f"Setting volume to {volume_level}%")
            
            # For Windows, use direct key simulation approach
            if volume_level == 0:
                # Mute if volume is 0
                pyautogui.press('volumemute')
                return True
                
            # Simplified approach - just use appropriate number of key presses
            # Each keypress is ~2% of volume
            presses = int(volume_level / 2)
            
            # Limit presses to reasonable range
            presses = min(presses, 50)  # Max 50 key presses
            
            # First mute to ensure we're starting from a known state
            pyautogui.press('volumemute')
            time.sleep(0.2)
            # Press again to unmute
            pyautogui.press('volumemute')
            time.sleep(0.2)
            
            # Then use volumeup to reach desired level
            for _ in range(presses):
                pyautogui.press('volumeup')
                time.sleep(0.05)
                
            print(f"Volume set to approximately {volume_level}%")
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False
            
    def _adjust_brightness(self, amount):
        """Adjust screen brightness by a relative amount"""
        try:
            print(f"Adjusting brightness by {amount}%")
            
            if platform.system() == 'Windows':
                try:
                    # Use Windows specific module for brightness control
                    import wmi
                    c = wmi.WMI(namespace='wmi')
                    
                    # Get current brightness
                    brightness_methods = c.WmiMonitorBrightnessMethods()[0]
                    brightness_info = c.WmiMonitorBrightness()[0]
                    current_brightness = brightness_info.CurrentBrightness
                    
                    # Calculate new brightness
                    new_brightness = max(0, min(100, current_brightness + amount))
                    
                    # Set new brightness
                    brightness_methods.WmiSetBrightness(new_brightness, 0)
                    print(f"Brightness changed from {current_brightness}% to {new_brightness}%")
                    return True
                except ImportError:
                    print("WMI module not found. Falling back to keyboard shortcuts.")
                    # Fall back to keyboard shortcuts
                except Exception as e:
                    print(f"Windows brightness control error: {e}")
                    # Fall back to keyboard shortcuts
            
            # Determine number of key presses (each press is ~10% brightness)
            presses = abs(int(amount / 10))
            presses = min(presses, 10)  # Limit to 10 presses max
            
            if amount > 0:
                # Try common brightness up shortcuts
                for _ in range(presses):
                    # Try multiple common shortcuts for different laptop models
                    try:
                        # HP laptops
                        pyautogui.hotkey('fn', 'f12')
                        time.sleep(0.1)
                    except:
                        pass
                    
                    try:
                        # Dell, Lenovo laptops
                        pyautogui.hotkey('fn', 'f11')
                        time.sleep(0.1)
                    except:
                        pass
                    
                    try:
                        # Other common laptops
                        pyautogui.hotkey('fn', 'f3')
                        time.sleep(0.1)
                    except:
                        pass
            else:
                # Try common brightness down shortcuts
                for _ in range(presses):
                    try:
                        # HP laptops
                        pyautogui.hotkey('fn', 'f11')
                        time.sleep(0.1)
                    except:
                        pass
                    
                    try:
                        # Dell, Lenovo laptops
                        pyautogui.hotkey('fn', 'f10')
                        time.sleep(0.1)
                    except:
                        pass
                    
                    try:
                        # Other common laptops
                        pyautogui.hotkey('fn', 'f2')
                        time.sleep(0.1)
                    except:
                        pass
                    
            print(f"Brightness adjusted by approximately {amount}%")
            return True
        except Exception as e:
            print(f"Error adjusting brightness: {e}")
            return False
            
    def _set_brightness(self, brightness_level):
        """Set screen brightness to a specific level (0-100)"""
        try:
            print(f"Setting brightness to {brightness_level}%")
            
            # Use simple key simulation approach
            # First try a shortcut to minimize brightness (different on various laptops)
            for _ in range(10):  # Try 10 times to ensure minimum
                pyautogui.hotkey('fn', 'f2')  # Common shortcut for brightness down
                time.sleep(0.1)
                
            # Then increase to desired level
            # Each keypress is ~10% brightness
            presses = int(brightness_level / 10)
            
            # Limit to reasonable range
            presses = min(presses, 10)  # Max 10 key presses
            
            for _ in range(presses):
                pyautogui.hotkey('fn', 'f3')  # Common shortcut for brightness up
                time.sleep(0.1)
                
            print(f"Brightness set to approximately {brightness_level}%")
            return True
        except Exception as e:
            print(f"Error setting brightness: {e}")
            return False

    def play_audio(self, audio_name=None):
        """Play audio from the audio directory"""
        try:
            # Clean up any existing playlist before creating a new one
            self._cleanup_playlist()
            
            # Get all audio files
            audio_files = []
            for ext in self.audio_extensions:
                audio_files.extend(glob.glob(os.path.join(self.audio_dir, f"*{ext}")))
            
            if not audio_files:
                speak("No audio files found in the audio directory. Please add some audio files to the media/audio folder.")
                return False
            
            # If audio name is specified, try to find a matching audio
            if audio_name:
                matching_files = []
                for file in audio_files:
                    if audio_name.lower() in os.path.basename(file).lower():
                        matching_files.append(file)
                
                if matching_files:
                    # Play the first matching audio
                    file_path = matching_files[0]
                    file_name = os.path.basename(file_path)
                    speak(f"Playing audio: {file_name}")
                else:
                    speak(f"Couldn't find audio matching '{audio_name}'. Playing a random audio file instead.")
                    file_path = random.choice(audio_files)
                    file_name = os.path.basename(file_path)
                    speak(f"Playing audio: {file_name}")
            else:
                # Play a random audio
                file_path = random.choice(audio_files)
                file_name = os.path.basename(file_path)
                speak(f"Playing random audio: {file_name}")
            
            # Open the audio with the default media player
            return self._open_media_file(file_path, self.default_audio_player)
                
        except Exception as e:
            print(f"Error playing audio: {e}")
            speak("Sorry, I couldn't play the audio.")
            return False
    
    def play_video(self, video_name=None):
        """Play video from the video directory"""
        try:
            # Clean up any existing playlist before creating a new one
            self._cleanup_playlist()
            
            # Get all video files
            video_files = []
            for ext in self.video_extensions:
                video_files.extend(glob.glob(os.path.join(self.video_dir, f"*{ext}")))
            
            if not video_files:
                speak("No video files found in the video directory. Please add some video files to the media/video folder.")
                return False
            
            # Check if user wants random videos
            is_random = video_name and "random" in video_name.lower()
            
            # If video name is specified, try to find a matching video
            if video_name and not is_random:
                matching_files = []
                for file in video_files:
                    if video_name.lower() in os.path.basename(file).lower():
                        matching_files.append(file)
                
                if matching_files:
                    # Play the first matching video
                    file_path = matching_files[0]
                    file_name = os.path.basename(file_path)
                    speak(f"Playing video: {file_name}")
                else:
                    speak(f"Couldn't find video matching '{video_name}'. Playing a random video file instead.")
                    file_path = random.choice(video_files)
                    file_name = os.path.basename(file_path)
                    speak(f"Playing video: {file_name}")
            elif is_random:
                # Play random videos (the playlist creation will handle selecting random videos)
                file_path = random.choice(video_files)
                speak("Playing random videos in playlist mode")
            else:
                # Play a random video
                file_path = random.choice(video_files)
                file_name = os.path.basename(file_path)
                speak(f"Playing random video: {file_name}")
            
            # Open the video with the default media player
            return self._open_media_file(file_path, self.default_video_player)
                
        except Exception as e:
            print(f"Error playing video: {e}")
            speak("Sorry, I couldn't play the video.")
            return False
    
    def play_music(self, song_name=None):
        """Legacy method for backward compatibility"""
        return self.play_audio(song_name)
    
    def take_screenshot(self):
        """Take a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
            pyautogui.screenshot(screenshot_path)
            speak("Screenshot taken successfully")
            return True
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            speak("Sorry, I couldn't take the screenshot.")
            return False
    
    def get_system_info(self):
        """Get system information including CPU, memory usage, battery, etc."""
        try:
            import psutil
            import platform
            
            # Get OS information
            os_info = platform.system() + " " + platform.version()
            
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_used = round(memory.used / (1024 * 1024 * 1024), 2)  # Convert to GB
            memory_total = round(memory.total / (1024 * 1024 * 1024), 2)  # Convert to GB
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_used = round(disk.used / (1024 * 1024 * 1024), 2)  # Convert to GB
            disk_total = round(disk.total / (1024 * 1024 * 1024), 2)  # Convert to GB
            disk_percent = disk.percent
            
            # Compile the information as a string with no formatting
            system_info = "Operating System: " + os_info + "\n"
            system_info += "CPU Usage: " + str(cpu_usage) + "%\n"
            system_info += "Memory Usage: " + str(memory_used) + " GB of " + str(memory_total) + " GB (" + str(memory_percent) + "%)\n"
            system_info += "Disk Usage: " + str(disk_used) + " GB of " + str(disk_total) + " GB (" + str(disk_percent) + "%)"
            
            # Get battery information if available
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    power_plugged = "plugged in" if battery.power_plugged else "not plugged in"
                    
                    # Calculate remaining time if not plugged in
                    if not battery.power_plugged and battery.secsleft > 0:
                        hours, remainder = divmod(battery.secsleft, 3600)
                        minutes, _ = divmod(remainder, 60)
                        remaining_time = str(int(hours)) + " hours and " + str(int(minutes)) + " minutes remaining"
                    else:
                        remaining_time = "charging"
                        
                    system_info += "\nBattery: " + str(battery_percent) + "% (" + power_plugged + ", " + remaining_time + ")"
            
            # Print the information
            print(system_info)
            
            # Speak only the most important parts using plain string concatenation
            speak("CPU Usage: " + str(int(cpu_usage)) + " percent, Memory: " + str(int(memory_percent)) + " percent, Disk: " + str(int(disk_percent)) + " percent")
            
            return True
        except Exception as e:
            print("Error retrieving system information: " + str(e))
            speak("Sorry, I couldn't retrieve your system information.")
            return False

    def get_battery_info(self):
        """Get detailed battery information"""
        try:
            import psutil
            
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    power_plugged = battery.power_plugged
                    
                    if power_plugged:
                        status = "charging"
                        print("Battery: " + str(battery_percent) + "% (" + status + ")")
                        speak("Battery is at " + str(int(battery_percent)) + " percent and " + status)
                    else:
                        # Calculate remaining time
                        if battery.secsleft > 0:
                            hours, remainder = divmod(battery.secsleft, 3600)
                            minutes, _ = divmod(remainder, 60)
                            remaining_time = str(int(hours)) + " hours and " + str(int(minutes)) + " minutes"
                            print("Battery: " + str(battery_percent) + "% (discharging, " + remaining_time + " remaining)")
                            speak("Battery is at " + str(int(battery_percent)) + " percent with approximately " + remaining_time + " remaining")
                        else:
                            print("Battery: " + str(battery_percent) + "%")
                            speak("Battery is at " + str(int(battery_percent)) + " percent")
                    return True
                else:
                    print("Battery information not available")
                    speak("Battery information is not available on this device")
                    return False
            else:
                print("Battery information not available")
                speak("Battery information is not available on this device")
                return False
        except Exception as e:
            print("Error retrieving battery information: " + str(e))
            speak("Sorry, I couldn't retrieve your battery information")
            return False

    def get_wifi_info(self):
        """Get Wi-Fi connection information"""
        try:
            import subprocess
            import re
            
            if platform.system() == 'Windows':
                try:
                    # Try a different approach - check if Wi-Fi is enabled first
                    print("Checking Wi-Fi status...")
                    
                    # Check network connections
                    result = subprocess.check_output("ipconfig", shell=True).decode('utf-8')
                    
                    # Look for wireless adapter information
                    wireless_sections = re.findall(r"Wireless LAN adapter.*?(?=\n\n)", result, re.DOTALL)
                    
                    if not wireless_sections:
                        print("No wireless adapters found")
                        speak("No wireless adapters were found on your system. You might not have Wi-Fi capabilities or the adapter is disabled")
                        return False
                    
                    # Extract information from the first wireless adapter section
                    wireless_info = wireless_sections[0]
                    
                    # Look for IP address
                    ip_match = re.search(r"IPv4 Address.*?:\s*(.+)", wireless_info)
                    ip_address = ip_match.group(1).strip() if ip_match else "Not connected"
                    
                    # Look for connection state
                    media_state_match = re.search(r"Media State.*?:\s*(.+)", wireless_info)
                    media_state = media_state_match.group(1).strip() if media_state_match else "Unknown"
                    
                    # Format response
                    if "Not connected" in ip_address or "Media disconnected" in media_state:
                        print("Wi-Fi is disconnected")
                        speak("You are not connected to any Wi-Fi network")
                    else:
                        print("Wi-Fi is connected with IP: " + ip_address)
                        speak("You are connected to Wi-Fi with IP address " + ip_address)
                    
                    return True
                except Exception as e:
                    print("Error checking Wi-Fi: " + str(e))
                    speak("I couldn't check your Wi-Fi status")
                    return False
            else:
                # For Linux/macOS
                try:
                    # Using different approach for Linux/macOS
                    if platform.system() == 'Darwin':  # macOS
                        result = subprocess.check_output("networksetup -getairportnetwork en0", shell=True).decode('utf-8')
                        network_name = re.search(r"Current Wi-Fi Network: (.+)", result)
                        if network_name:
                            ssid = network_name.group(1).strip()
                            print("Connected to Wi-Fi network: " + ssid)
                            speak("You are connected to the " + ssid + " Wi-Fi network")
                            return True
                        else:
                            print("Not connected to any Wi-Fi network")
                            speak("You are not connected to any Wi-Fi network")
                            return False
                    else:  # Linux
                        result = subprocess.check_output("iwconfig 2>/dev/null | grep ESSID", shell=True).decode('utf-8')
                        network_name = re.search(r'ESSID:"(.+)"', result)
                        if network_name:
                            ssid = network_name.group(1).strip()
                            print("Connected to Wi-Fi network: " + ssid)
                            speak("You are connected to the " + ssid + " Wi-Fi network")
                            return True
                        else:
                            print("Not connected to any Wi-Fi network")
                            speak("You are not connected to any Wi-Fi network")
                            return False
                except Exception as e:
                    print("Error checking Wi-Fi: " + str(e))
                    speak("I couldn't check your Wi-Fi status")
                    return False
        except Exception as e:
            print("Error retrieving Wi-Fi information: " + str(e))
            speak("Sorry, I couldn't retrieve your Wi-Fi information")
            return False
    
    def cleanup(self):
        """Clean up resources when the application exits"""
        try:
            self.stop_media()
            self._cleanup_playlist()
            print("Advanced features cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
    def __del__(self):
        """Destructor to ensure cleanup when object is destroyed"""
        self.cleanup()

    def get_weather_info(self, city):
        """Get weather information using web search"""
        try:
            search_query = f"weather in {city} today"
            speak(f"Searching for weather information in {city}")
            return search_web(search_query, speak_result=True)
        except Exception as e:
            print(f"Error getting weather info: {e}")
            speak("Sorry, I couldn't get the weather information.")
            return False

    def get_news(self):
        """Get news using web search"""
        try:
            search_query = "latest news headlines today"
            speak("Searching for the latest news")
            return search_web(search_query, speak_result=True)
        except Exception as e:
            print(f"Error getting news: {e}")
            speak("Sorry, I couldn't get the latest news.")
            return False 