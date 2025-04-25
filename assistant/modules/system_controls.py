#!/usr/bin/env python
import os
import subprocess
import webbrowser
import logging
import re
import platform
import time
import psutil
import pyautogui
import datetime
import wmi  # For Windows-specific features
from pathlib import Path
import urllib.request
import glob
import requests

# Handle imports with fallback
try:
    from assistant.modules.speech_utils import speak
except ImportError:
    try:
        from speech_utils import speak
    except ImportError:
        # Create a dummy speak function if imports fail
        def speak(text):
            print(f"[SPEECH]: {text}")

# Set up logging
logger = logging.getLogger(__name__)

# Common Windows applications with their executable names
WINDOWS_APPS = {
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'chrome': 'chrome.exe',
    'google chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'word': 'winword.exe',
    'excel': 'excel.exe',
    'powerpoint': 'powerpnt.exe',
    'paint': 'mspaint.exe',
    'file explorer': 'explorer.exe',
    'explorer': 'explorer.exe',
    'cmd': 'cmd.exe',
    'command prompt': 'cmd.exe',
    'terminal': 'cmd.exe',
    'powershell': 'powershell.exe',
    'control panel': 'control.exe',
    'task manager': 'taskmgr.exe',
    'spotify': 'spotify.exe',
    'vlc': 'vlc.exe',
    'edge': 'msedge.exe',
    'microsoft edge': 'msedge.exe',
    'outlook': 'OUTLOOK.EXE',
    'settings': 'ms-settings:',
    'vscode': 'code.exe',
    'visual studio code': 'code.exe',
    'discord': 'discord.exe',
    'skype': 'skype.exe',
    'zoom': 'zoom.exe'
}

# Common installation paths for applications
APP_PATHS = {
    'chrome.exe': [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ],
    'firefox.exe': [
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
    ],
    'msedge.exe': [
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
    ]
}

class SystemControls:
    """Class to handle system control operations like app launching, shutdown, etc."""
    
    def __init__(self):
        """Initialize SystemControls instance"""
        self.windows_apps = WINDOWS_APPS
        self.app_paths = APP_PATHS
        self.os_name = platform.system()
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "Pictures", "AI_Assistant_Screenshots")
        
        # Create screenshots directory if it doesn't exist
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir, exist_ok=True)
            
        # Initialize WMI for Windows-specific features
        if self.os_name == 'Windows':
            try:
                self.wmi = wmi.WMI()
            except Exception as e:
                logger.error(f"Error initializing WMI: {e}")
                self.wmi = None
    
    def extract_app_name(self, command):
        """Extract application name from command"""
        command = command.lower()
        
        # Extract application name using regex
        app_patterns = [
            r'open\s+(.+?)(?:\s+for me|\s+now|\s+please|\s+app|\s+application|$)',
            r'launch\s+(.+?)(?:\s+for me|\s+now|\s+please|\s+app|\s+application|$)',
            r'start\s+(.+?)(?:\s+for me|\s+now|\s+please|\s+app|\s+application|$)',
            r'run\s+(.+?)(?:\s+for me|\s+now|\s+please|\s+app|\s+application|$)'
        ]
        
        for pattern in app_patterns:
            match = re.search(pattern, command)
            if match:
                app_name = match.group(1).strip()
                logger.info(f"Extracted app name: '{app_name}' from command: '{command}'")
                return app_name
        
        # If no app name found with regex, check for direct mentions
        for app_name in self.windows_apps:
            if app_name in command:
                logger.info(f"Found app name: '{app_name}' directly in command: '{command}'")
                return app_name
                
        return None

    def find_executable_path(self, executable):
        """Find the full path of an executable"""
        # Check if we have predefined paths for this executable
        if executable in self.app_paths:
            for path in self.app_paths[executable]:
                if os.path.exists(path):
                    return path
        
        # Try to find in PATH
        if platform.system() == 'Windows':
            # Windows: Check Program Files directories
            for program_files in ['C:\\Program Files', 'C:\\Program Files (x86)']:
                for root, dirs, files in os.walk(program_files):
                    if executable in files:
                        return os.path.join(root, executable)
        
        # Return just the executable name and let the system find it
        return executable
    
    def get_date_time(self, command):
        """Handle date and time related commands"""
        now = datetime.datetime.now()
        
        if "time" in command and "date" not in command:
            print(f"Command: {command} | Category: system_info | Confidence: 0.95")
            time_str = now.strftime("%I:%M %p")
            speak(f"The current time is {time_str}")
            return True
        elif "date" in command and "time" not in command:
            print(f"Command: {command} | Category: system_info | Confidence: 0.95")
            date_str = now.strftime("%A, %B %d, %Y")
            speak(f"Today is {date_str}")
            return True
        else:
            # Both date and time
            print(f"Command: {command} | Category: system_info | Confidence: 0.95")
            date_time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
            speak(f"It's {date_time_str}")
            return True
    
    def get_system_info(self, command):
        """Handle system information requests"""
        print(f"Command: {command} | Category: system_info | Confidence: 0.95")
        try:
            command = command.lower()
            
            # CPU information
            if any(word in command for word in ["cpu", "processor", "processing"]):
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count(logical=True)
                cpu_freq = psutil.cpu_freq()
                
                print(f"CPU Usage: {cpu_percent}%")
                print(f"CPU Cores: {cpu_count}")
                if cpu_freq:
                    print(f"CPU Frequency: {cpu_freq.current:.2f} MHz")
                
                speak(f"CPU usage is {cpu_percent} percent across {cpu_count} logical cores")
                return True
            
            # Memory information
            elif any(word in command for word in ["memory", "ram", "memory usage"]):
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024 * 1024 * 1024)
                used_gb = memory.used / (1024 * 1024 * 1024)
                
                print(f"Memory Usage: {memory.percent}%")
                print(f"Used: {used_gb:.1f} GB / Total: {total_gb:.1f} GB")
                
                speak(f"Memory usage is {memory.percent} percent, using {used_gb:.1f} gigabytes out of {total_gb:.1f}")
                return True
            
            # Disk information
            elif any(word in command for word in ["disk", "storage", "drive", "space"]):
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if partition.fstype:
                        usage = psutil.disk_usage(partition.mountpoint)
                        total_gb = usage.total / (1024 * 1024 * 1024)
                        used_gb = usage.used / (1024 * 1024 * 1024)
                        
                        print(f"\nDrive {partition.device}:")
                        print(f"Usage: {usage.percent}%")
                        print(f"Used: {used_gb:.1f} GB / Total: {total_gb:.1f} GB")
                        
                        if partition.device.startswith("C:"):
                            speak(f"Your main drive is {usage.percent} percent full, using {used_gb:.1f} gigabytes")
                return True
            
            # Temperature information (if available)
            elif any(word in command for word in ["temperature", "temp", "heat"]):
                try:
                    temperatures = psutil.sensors_temperatures()
                    if temperatures:
                        for name, entries in temperatures.items():
                            for entry in entries:
                                print(f"{name}: {entry.current}°C")
                                speak(f"Current temperature is {entry.current:.1f} degrees Celsius")
                                return True
                    speak("Temperature information is not available")
                except:
                    speak("Temperature information is not available")
                return True
            
            # General system information
            else:
                system = platform.uname()
                boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.datetime.now() - boot_time
                
                print(f"System: {system.system} {system.release}")
                print(f"Machine: {system.machine}")
                print(f"Processor: {system.processor}")
                print(f"Uptime: {uptime.days} days, {uptime.seconds//3600} hours")
                
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                speak(f"You are running {system.system} {system.release}. CPU usage is {cpu_percent} percent and memory usage is {memory.percent} percent")
                return True
                
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            speak("Sorry, I couldn't retrieve system information")
            return False
    
    def get_battery_info(self):
        """Get battery information"""
        try:
            print(f"Command: battery | Category: system_info | Confidence: 0.95")
            battery = psutil.sensors_battery()
            
            if not battery:
                logger.error("Could not retrieve battery information")
                print("Battery information not available")
                speak("Battery information is not available on this device")
                return False
            
            # Get battery percentage
            percent = battery.percent
            
            # Get charging status
            power_plugged = battery.power_plugged
            status = "Charging" if power_plugged else "Discharging"
            
            # Calculate time remaining
            time_left = ""
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                # Convert seconds to hours and minutes
                hours, remainder = divmod(battery.secsleft, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if hours > 0:
                    time_left = f"{hours} hours and {minutes} minutes"
                else:
                    time_left = f"{minutes} minutes"
                
                if power_plugged:
                    time_left = f"Fully charged in {time_left}"
                else:
                    time_left = f"Time remaining: {time_left}"
            
            # Get battery health description
            health = "Unknown"
            if percent >= 80:
                health = "Excellent"
            elif percent >= 60:
                health = "Good"
            elif percent >= 40:
                health = "Fair"
            elif percent >= 20:
                health = "Low"
            else:
                health = "Critical"
            
            # Try to get power plan
            power_plan = "Unknown"
            if os.name == 'nt':  # Windows
                try:
                    result = subprocess.run(["powercfg", "/GETACTIVESCHEME"], 
                                           capture_output=True, text=True, check=True)
                    power_plan_match = re.search(r'\((.*?)\)$', result.stdout.strip())
                    if power_plan_match:
                        power_plan = power_plan_match.group(1)
                except:
                    pass
            
            # Format and print information
            logger.info(f"Battery: {percent}% - {status}")
            print(f"Battery: {percent}% ({health}) - {status}")
            if time_left:
                print(f"{time_left}")
            print(f"Power Plan: {power_plan}")
            
            # Speak basic battery information
            speak(f"Battery is at {percent} percent and is {status.lower()}. Battery health is {health}.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error getting battery info: {e}")
            speak("I couldn't retrieve battery information")
            return False
    
    def get_wifi_info(self):
        """Get detailed WiFi information"""
        try:
            print(f"Command: wifi | Category: system_info | Confidence: 0.95")
            
            # Different approaches based on operating system
            if platform.system() == 'Windows':
                # Use netsh to get wifi info on Windows
                try:
                    wifi_interfaces = subprocess.check_output(
                        ['netsh', 'wlan', 'show', 'interfaces'], 
                        universal_newlines=True
                    )
                    
                    # Check if connected to WiFi
                    if "State" in wifi_interfaces and "connected" in wifi_interfaces.lower():
                        # Get detailed network info
                        wifi_info = subprocess.check_output(
                            ['netsh', 'wlan', 'show', 'network', 'mode=Bssid'], 
                            universal_newlines=True
                        )
                        
                        # Extract SSID
                        ssid_match = re.search(r"SSID\s+\d+\s+:\s(.*)", wifi_interfaces)
                        ssid = ssid_match.group(1).strip() if ssid_match else "Unknown"
                        
                        # Extract signal strength
                        signal_match = re.search(r"Signal\s+:\s(.*)", wifi_interfaces)
                        signal = signal_match.group(1).strip() if signal_match else "Unknown"
                        
                        # Extract authentication type
                        auth_match = re.search(r"Authentication\s+:\s(.*)", wifi_interfaces)
                        auth = auth_match.group(1).strip() if auth_match else "Unknown"
                        
                        # Extract channel
                        channel_match = re.search(r"Channel\s+:\s(.*)", wifi_interfaces)
                        channel = channel_match.group(1).strip() if channel_match else "Unknown"
                        
                        # Extract radio type (802.11n, ac, etc.)
                        radio_match = re.search(r"Radio type\s+:\s(.*)", wifi_interfaces)
                        radio_type = radio_match.group(1).strip() if radio_match else "Unknown"
                        
                        # Get network speed
                        speed_match = re.search(r"Receive rate\s*\(Mbps\)\s*:\s(.*)", wifi_interfaces)
                        speed = speed_match.group(1).strip() if speed_match else "Unknown"
                        
                        # Check if internet is actually working
                        internet_status = "Connected"
                        try:
                            # Try to connect to a reliable host
                            urllib.request.urlopen("https://www.google.com", timeout=3)
                        except:
                            internet_status = "Limited or no internet access"
                        
                        # Format the output with color coding for signal strength
                        color_prefix = ""
                        if "%" in signal:
                            signal_percent = int(signal.replace("%", ""))
                            if signal_percent >= 80:
                                color_prefix = "\033[92m"  # Green for excellent
                            elif signal_percent >= 50:
                                color_prefix = "\033[93m"  # Yellow for good
                            else:
                                color_prefix = "\033[91m"  # Red for poor
                        
                        # Format and print the WiFi information
                        wifi_status = (
                            f"{color_prefix}WiFi Status: Connected to {ssid}\033[0m\n"
                            f"Signal Strength: {signal}\n"
                            f"Speed: {speed} Mbps\n"
                            f"Channel: {channel}\n"
                            f"Radio Type: {radio_type}\n"
                            f"Authentication: {auth}\n"
                            f"Internet: {internet_status}"
                        )
                        
                        print(wifi_status)
                        logger.info(f"WiFi: Connected to {ssid}, Signal: {signal}, Internet: {internet_status}")
                        return True
                    else:
                        print("WiFi Status: Not connected to any network")
                        logger.info("WiFi: Not connected")
                        return False
                        
                except subprocess.SubprocessError as e:
                    logger.error(f"Error retrieving Windows WiFi information: {e}")
                    print("WiFi Status: Unable to retrieve information")
                    return False
            
            elif platform.system() == 'Linux':
                try:
                    # Try using nmcli first (NetworkManager)
                    nmcli_output = subprocess.check_output(
                        ['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,BARS,SECURITY,DEVICE', 'device', 'wifi'], 
                        universal_newlines=True
                    )
                    
                    # Find the active connection
                    for line in nmcli_output.strip().split('\n'):
                        if line.startswith('yes:'):
                            parts = line.split(':')
                            if len(parts) >= 6:
                                ssid = parts[1]
                                signal = parts[2] + '%'
                                bars = parts[3]  # Signal quality indicator
                                security = parts[4]
                                device = parts[5]
                                
                                # Get IP information
                                ip_info = subprocess.check_output(
                                    ['ip', 'addr', 'show', device], 
                                    universal_newlines=True
                                )
                                
                                ip_match = re.search(r"inet\s([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", ip_info)
                                ip_address = ip_match.group(1) if ip_match else "Unknown"
                                
                                # Format the output with color coding
                                signal_percent = int(signal.replace("%", ""))
                                if signal_percent >= 80:
                                    color_prefix = "\033[92m"  # Green for excellent
                                elif signal_percent >= 50:
                                    color_prefix = "\033[93m"  # Yellow for good
                                else:
                                    color_prefix = "\033[91m"  # Red for poor
                                
                                wifi_status = (
                                    f"{color_prefix}WiFi Status: Connected to {ssid}\033[0m\n"
                                    f"Signal Strength: {signal} ({bars})\n"
                                    f"Security: {security}\n"
                                    f"Interface: {device}\n"
                                    f"IP Address: {ip_address}"
                                )
                                
                                print(wifi_status)
                                logger.info(f"WiFi: Connected to {ssid}, Signal: {signal}, IP: {ip_address}")
                                return True
                    
                    print("WiFi Status: Not connected to any network")
                    return False
                    
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Fallback to iwconfig if nmcli fails
                    try:
                        iwconfig_output = subprocess.check_output(
                            ['iwconfig'],
                            universal_newlines=True,
                            stderr=subprocess.STDOUT
                        )
                        
                        # Parse iwconfig output
                        ssid_match = re.search(r'ESSID:"([^"]*)"', iwconfig_output)
                        ssid = ssid_match.group(1) if ssid_match else "Not connected"
                        
                        if ssid != "Not connected":
                            signal_match = re.search(r'Signal level=(.*) dBm', iwconfig_output)
                            signal = signal_match.group(1) if signal_match else "Unknown"
                            
                            # Calculate approximate percentage from dBm
                            if "dBm" in signal:
                                try:
                                    dbm = float(signal.replace("dBm", "").strip())
                                    # Convert dBm to percentage (approx.): -50dBm→100%, -100dBm→0%
                                    signal_percent = max(0, min(100, 2 * (dbm + 100)))
                                    signal = f"{int(signal_percent)}% ({dbm} dBm)"
                                except:
                                    pass
                            
                            wifi_status = f"WiFi Status: Connected to {ssid}\nSignal Strength: {signal}"
                            print(wifi_status)
                            logger.info(f"WiFi: Connected to {ssid}, Signal: {signal}")
                            return True
                        else:
                            print("WiFi Status: Not connected to any network")
                            return False
                            
                    except (subprocess.SubprocessError, FileNotFoundError) as e:
                        logger.error(f"Error retrieving Linux WiFi information: {e}")
                        print("WiFi Status: Unable to retrieve information")
                        return False
            
            elif platform.system() == 'Darwin':  # macOS
                try:
                    # Get network interface info
                    airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
                    
                    # Check if airport command is available
                    if os.path.exists(airport_path):
                        airport_output = subprocess.check_output(
                            [airport_path, '-I'],
                            universal_newlines=True
                        )
                        
                        # Parse the output
                        ssid_match = re.search(r'\s+SSID: (.*)', airport_output)
                        ssid = ssid_match.group(1) if ssid_match else "Not connected"
                        
                        if ssid != "Not connected":
                            # Extract other information
                            bssid_match = re.search(r'\s+BSSID: (.*)', airport_output)
                            bssid = bssid_match.group(1) if bssid_match else "Unknown"
                            
                            rssi_match = re.search(r'\s+agrCtlRSSI: (.*)', airport_output)
                            rssi = rssi_match.group(1) if rssi_match else "Unknown"
                            
                            channel_match = re.search(r'\s+channel: (.*)', airport_output)
                            channel = channel_match.group(1) if channel_match else "Unknown"
                            
                            # Calculate signal percentage (macOS reports RSSI)
                            try:
                                rssi_val = int(rssi)
                                # Convert RSSI to percentage (approx.): -50→100%, -100→0%
                                signal_percent = max(0, min(100, 2 * (rssi_val + 100)))
                                signal = f"{signal_percent}% ({rssi} dBm)"
                            except:
                                signal = rssi
                            
                            # Format the output with color
                            color_prefix = ""
                            if signal_percent >= 80:
                                color_prefix = "\033[92m"  # Green for excellent
                            elif signal_percent >= 50:
                                color_prefix = "\033[93m"  # Yellow for good
                            else:
                                color_prefix = "\033[91m"  # Red for poor
                            
                            wifi_status = (
                                f"{color_prefix}WiFi Status: Connected to {ssid}\033[0m\n"
                                f"Signal Strength: {signal}\n"
                                f"BSSID: {bssid}\n"
                                f"Channel: {channel}"
                            )
                            
                            print(wifi_status)
                            logger.info(f"WiFi: Connected to {ssid}, Signal: {signal}")
                            return True
                        else:
                            print("WiFi Status: Not connected to any network")
                            return False
                    else:
                        # Fallback to networksetup if airport command not available
                        interfaces = subprocess.check_output(
                            ['networksetup', '-listallhardwareports'],
                            universal_newlines=True
                        )
                        
                        # Find Wi-Fi interface
                        wifi_match = re.search(r'Hardware Port: Wi-Fi\nDevice: (.*)', interfaces)
                        if wifi_match:
                            interface = wifi_match.group(1).strip()
                            
                            # Get current network
                            network = subprocess.check_output(
                                ['networksetup', '-getairportnetwork', interface],
                                universal_newlines=True
                            )
                            
                            ssid_match = re.search(r'Current Wi-Fi Network: (.*)', network)
                            ssid = ssid_match.group(1).strip() if ssid_match else "Not connected"
                            
                            if ssid != "Not connected":
                                wifi_status = f"WiFi Status: Connected to {ssid}"
                                print(wifi_status)
                                logger.info(f"WiFi: Connected to {ssid}")
                                return True
                            else:
                                print("WiFi Status: Not connected to any network")
                                return False
                        else:
                            print("WiFi Status: No Wi-Fi interface found")
                            return False
                
                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    logger.error(f"Error retrieving macOS WiFi information: {e}")
                    print("WiFi Status: Unable to retrieve information")
                    return False
            
            else:
                print(f"WiFi Status: Unsupported operating system ({platform.system()})")
                return False
                
        except Exception as e:
            logger.error(f"Error getting WiFi information: {e}")
            print("Could not retrieve WiFi information")
            return False
    
    def control_window(self, command):
        """Handle window control commands"""
        try:
            command = command.lower()
            
            # Window minimize commands
            if any(phrase in command for phrase in ["minimize", "make small", "shrink window", "minimize window"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                pyautogui.hotkey('win', 'down')  # Windows + Down Arrow
                speak("Window minimized")
                return True
            
            # Window maximize commands
            elif any(phrase in command for phrase in ["maximize", "make big", "full screen", "maximize window"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                pyautogui.hotkey('win', 'up')  # Windows + Up Arrow
                speak("Window maximized")
                return True
            
            # Window restore commands
            elif any(phrase in command for phrase in ["restore", "normal size", "restore window", "normal window"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                pyautogui.hotkey('win', 'down')  # Windows + Down Arrow
                speak("Window restored")
                return True
            
            # Window close commands
            elif any(phrase in command for phrase in ["close window", "close this", "close current window"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                pyautogui.hotkey('alt', 'f4')
                speak("Window closed")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error controlling window: {e}")
            return False
    
    def launch_application(self, command):
        """Launch an application based on the command"""
        app_name = self.extract_app_name(command)
        
        if app_name:
            print(f"Command: {command} | Category: system_control | Confidence: 0.85")
            # Map app name to executable
            executable = self.windows_apps.get(app_name.lower(), app_name)
            
            # Try to find the full path
            executable_path = self.find_executable_path(executable)
            
            if executable_path:
                # Launch the application
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(executable_path)
                    else:  # Linux/Mac
                        subprocess.Popen([executable_path], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                    speak(f"Opening {app_name}")
                    return True
                except Exception as e:
                    logger.error(f"Error launching application: {e}")
                    speak(f"I couldn't open {app_name}. The application might not be installed.")
                    return False
            else:
                # If executable not found, suggest searching for it
                speak(f"I couldn't find {app_name} on your system. Would you like to search for it online?")
                time.sleep(1)  # Wait for a second for better UX
                from ..modules.web_search import search_web
                return search_web(f"download {app_name}")
        
        return False
    
    def system_power_control(self, command):
        """Handle system power controls like shutdown, restart, etc."""
        if "shutdown" in command or "power off" in command or "turn off" in command:
            print(f"Command: {command} | Category: system_control | Confidence: 0.95")
            speak("Are you sure you want to shut down your computer?")
            confirmation = input("Confirm shutdown (yes/no): ").strip().lower()
            if confirmation in ["yes", "y"]:
                speak("Shutting down your computer. Goodbye!")
                if os.name == 'nt':  # Windows
                    os.system("shutdown /s /t 5")
                else:  # Linux/Mac
                    os.system("sudo shutdown -h now")
                return True
            else:
                speak("Shutdown cancelled")
                return False
                
        elif "restart" in command or "reboot" in command:
            print(f"Command: {command} | Category: system_control | Confidence: 0.95")
            speak("Are you sure you want to restart your computer?")
            confirmation = input("Confirm restart (yes/no): ").strip().lower()
            if confirmation in ["yes", "y"]:
                speak("Restarting your computer. See you soon!")
                if os.name == 'nt':  # Windows
                    os.system("shutdown /r /t 5")
                else:  # Linux/Mac
                    os.system("sudo reboot")
                return True
            else:
                speak("Restart cancelled")
                return False
                
        elif "log off" in command or "sign out" in command:
            print(f"Command: {command} | Category: system_control | Confidence: 0.95")
            speak("Are you sure you want to log off?")
            confirmation = input("Confirm log off (yes/no): ").strip().lower()
            if confirmation in ["yes", "y"]:
                speak("Logging off. Goodbye!")
                if os.name == 'nt':  # Windows
                    os.system("shutdown /l")
                else:  # Linux/Mac
                    os.system("pkill -KILL -u $USER")
                return True
            else:
                speak("Log off cancelled")
                return False
                
        elif "lock" in command and ("computer" in command or "pc" in command or "system" in command):
            print(f"Command: {command} | Category: system_control | Confidence: 0.95")
            speak("Locking your computer.")
            if os.name == 'nt':  # Windows
                os.system("rundll32.exe user32.dll,LockWorkStation")
            else:  # Linux/Mac
                os.system("gnome-screensaver-command -l")
            return True
        
        return False

    def take_screenshot(self):
        """Capture a screenshot and save it to the screenshots directory"""
        try:
            # Check if pyautogui is properly initialized
            if not pyautogui.FAILSAFE:
                pyautogui.FAILSAFE = True
            
            # Ensure screenshot directory exists and is writable
            if not os.path.exists(self.screenshot_dir):
                os.makedirs(self.screenshot_dir, exist_ok=True)
                logger.info(f"Created screenshot directory: {self.screenshot_dir}")
            
            if not os.access(self.screenshot_dir, os.W_OK):
                logger.error(f"Screenshot directory is not writable: {self.screenshot_dir}")
                speak("I don't have permission to save screenshots in the Pictures folder")
                return False
            
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot with error handling
            try:
                # Add a small delay to ensure any UI elements are hidden
                time.sleep(0.5)
                screenshot = pyautogui.screenshot()
                if screenshot is None:
                    raise Exception("Screenshot capture failed")
            except Exception as e:
                logger.error(f"Failed to capture screenshot: {e}")
                speak("I couldn't capture the screen")
                return False
            
            # Save screenshot with error handling
            try:
                screenshot.save(filepath)
                logger.info(f"Screenshot saved successfully to: {filepath}")
            except Exception as e:
                logger.error(f"Failed to save screenshot: {e}")
                speak("I couldn't save the screenshot")
                return False
            
            print(f"Screenshot saved to: {filepath}")
            speak("Screenshot captured and saved")
            
            # Open the screenshot for viewing
            try:
                if self.os_name == "Windows":
                    os.startfile(filepath)
                elif self.os_name == "Darwin":  # macOS
                    subprocess.call(["open", filepath])
                else:  # Linux
                    subprocess.call(["xdg-open", filepath])
            except Exception as e:
                logger.error(f"Failed to open screenshot: {e}")
                # Don't return False here as the screenshot was still captured successfully
            
            return True
                
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            speak("I couldn't take a screenshot")
            return False

    def adjust_brightness(self, command):
        """Adjust screen brightness"""
        try:
            print(f"Command: {command} | Category: system_control | Confidence: 0.95")
            command = command.lower()
            
            # Check platform support
            if platform.system() != 'Windows':
                speak("Brightness control is only supported on Windows")
                return False
                
            # Get current brightness
            current_brightness = None
            try:
                import wmi
                c = wmi.WMI(namespace='wmi')
                method = c.WmiMonitorBrightnessMethods()[0]
                brightness_settings = c.WmiMonitorBrightness()[0]
                current_brightness = brightness_settings.CurrentBrightness
                print(f"Current brightness: {current_brightness}%")
            except Exception as e:
                logger.error(f"Error getting current brightness: {e}")
                speak("Unable to get current brightness")
                return False
                
            # Parse command for target brightness
            target_brightness = None
            
            # Check for explicit percentage - enhanced patterns
            # Match patterns like: "70%", "70 percent", "to 70%", "to 70 percent", "set to 70%"
            percent_match = re.search(r'(?:to |set to |at |set at |)(\d+)(\s*%|\s*percent)', command)
            if percent_match:
                target_brightness = int(percent_match.group(1))
                logger.info(f"Extracted brightness level: {target_brightness}% from command: '{command}'")
                
            # Check for brightness level words
            elif "maximum" in command or "max" in command or "full" in command:
                target_brightness = 100
            elif "minimum" in command or "min" in command:
                target_brightness = 10  # Not setting to 0 for safety
            elif "half" in command or "50" in command:
                target_brightness = 50
                
            # Check for increase/decrease commands
            elif "increase" in command or "up" in command or "higher" in command or "brighter" in command:
                # Default increase by 10%
                amount = 10
                
                # Check if a specific amount is mentioned
                amount_match = re.search(r'by\s+(\d+)', command)
                if amount_match:
                    amount = int(amount_match.group(1))
                    
                target_brightness = min(100, current_brightness + amount)
                
                print(f"Set brightness to {target_brightness}%")
                method.WmiSetBrightness(target_brightness, 0)
                speak(f"Brightness increased to {target_brightness} percent")
                return True
                
            elif "decrease" in command or "down" in command or "lower" in command or "dimmer" in command:
                # Default decrease by 10%
                amount = 10
                
                # Check if a specific amount is mentioned
                amount_match = re.search(r'by\s+(\d+)', command)
                if amount_match:
                    amount = int(amount_match.group(1))
                    
                target_brightness = max(0, current_brightness - amount)
                
                print(f"Set brightness to {target_brightness}%")
                method.WmiSetBrightness(target_brightness, 0)
                speak(f"Brightness decreased to {target_brightness} percent")
                return True
            
            # If we have a target brightness, set it
            if target_brightness is not None:
                # Ensure brightness is within valid range
                target_brightness = max(0, min(100, target_brightness))
                
                try:
                    print(f"Setting brightness to {target_brightness}%")
                    method.WmiSetBrightness(target_brightness, 0)
                    speak(f"Brightness set to {target_brightness} percent")
                    return True
                except Exception as set_error:
                    logger.error(f"Error setting brightness via WMI: {set_error}")
                    # Try alternative method using PowerShell
                    try:
                        ps_script = f"""
                        $brightness = {target_brightness};
                        $monitors = Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightnessMethods;
                        $monitors | ForEach-Object {{ $_.WmiSetBrightness(1, $brightness) }};
                        """
                        result = subprocess.run(['powershell', '-Command', ps_script], 
                                               capture_output=True, text=True)
                        if result.returncode == 0:
                            speak(f"Brightness set to {target_brightness} percent")
                            return True
                        else:
                            logger.error(f"PowerShell brightness error: {result.stderr}")
                            speak("I couldn't adjust the brightness using PowerShell")
                            return False
                    except Exception as ps_error:
                        logger.error(f"Error with PowerShell brightness: {ps_error}")
                        speak("I couldn't adjust the brightness. Your system might not support this feature.")
                        return False
            else:
                logger.warning(f"Couldn't extract brightness level from: {command}")
                speak("I couldn't determine what brightness level you want")
                return False
                
        except Exception as e:
            logger.error(f"Error adjusting brightness: {e}")
            speak("I couldn't adjust the brightness")
            return False

    def adjust_volume(self, command):
        """Adjust system volume"""
        try:
            # Parse the command to extract volume level
            volume_level = None
            
            # Check for percentage in command
            percentage_match = re.search(r'(\d+)(?:\s+)?(%|percent)', command)
            if percentage_match:
                volume_level = int(percentage_match.group(1))
            
            # Check for up/down/increase/decrease with optional amount
            increment_match = re.search(r'(?:up|increase)(?: by)? (\d+)', command)
            decrement_match = re.search(r'(?:down|decrease)(?: by)? (\d+)', command)
            
            if increment_match:
                increment_amount = int(increment_match.group(1))
                increment_presses = max(1, increment_amount // 5)  # Approximately 5% per press
                for _ in range(increment_presses):
                    pyautogui.press('volumeup')
                logger.info(f"Increased volume by approximately {increment_amount}%")
                print(f"Volume increased by approximately {increment_amount}%")
                return True
            elif decrement_match:
                decrement_amount = int(decrement_match.group(1))
                decrement_presses = max(1, decrement_amount // 5)  # Approximately 5% per press
                for _ in range(decrement_presses):
                    pyautogui.press('volumedown')
                logger.info(f"Decreased volume by approximately {decrement_amount}%")
                print(f"Volume decreased by approximately {decrement_amount}%")
                return True
            elif any(word in command for word in ['up', 'increase']):
                # Determine the increment amount (default to 10%)
                increment_amount = 10
                increment_presses = max(1, increment_amount // 5)  # Approximately 5% per press
                for _ in range(increment_presses):
                    pyautogui.press('volumeup')
                logger.info(f"Increased volume by approximately {increment_amount}%")
                print(f"Volume increased by approximately {increment_amount}%")
                return True
            elif any(word in command for word in ['down', 'decrease']):
                # Determine the decrement amount (default to 10%)
                decrement_amount = 10
                decrement_presses = max(1, decrement_amount // 5)  # Approximately 5% per press
                for _ in range(decrement_presses):
                    pyautogui.press('volumedown')
                logger.info(f"Decreased volume by approximately {decrement_amount}%")
                print(f"Volume decreased by approximately {decrement_amount}%")
                return True
            elif 'mute' in command or 'unmute' in command:
                # Toggle mute
                pyautogui.press('volumemute')
                logger.info("Toggled mute")
                print("Volume muted/unmuted")
                return True
            elif volume_level is not None:
                # For setting specific volume levels, use platform-specific methods
                if os.name == 'nt':  # Windows
                    try:
                        # Try using pycaw first for precise control
                        try:
                            from ctypes import cast, POINTER
                            from comtypes import CLSCTX_ALL
                            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                            
                            devices = AudioUtilities.GetSpeakers()
                            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                            volume = cast(interface, POINTER(IAudioEndpointVolume))
                            
                            # Set volume (value between 0.0 and 1.0)
                            volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
                            logger.info(f"Set volume to {volume_level}%")
                            print(f"Volume set to {volume_level}%")
                            return True
                        except Exception as pycaw_error:
                            logger.info(f"Could not use pycaw: {pycaw_error}, trying PowerShell method")
                            
                            # Fallback to PowerShell
                            ps_command = f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173); Start-Sleep -Milliseconds 50; "
                            # First mute to get to 0 volume
                            subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
                            
                            # Calculate how many volume up key presses needed (assume each press is about 2%)
                            presses = int(volume_level / 2)
                            ps_command = f"$obj = New-Object -ComObject WScript.Shell; "
                            for _ in range(presses):
                                ps_command += "$obj.SendKeys([char]175); Start-Sleep -Milliseconds 50; "
                            
                            subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
                            logger.info(f"Set volume to approximately {volume_level}% using PowerShell")
                            print(f"Volume set to approximately {volume_level}%")
                            return True
                    except Exception as win_error:
                        logger.error(f"Error setting specific volume with Windows methods: {win_error}")
                        # Fallback to key presses simulation
                        # Attempt to reset volume first
                        for _ in range(50):  # Ensure we go to zero
                            pyautogui.press('volumedown')
                        time.sleep(0.5)
                        
                        # Increase to target level (assume each press is about 2%)
                        presses = int(volume_level / 2)
                        for _ in range(presses):
                            pyautogui.press('volumeup')
                            time.sleep(0.05)  # Small delay between presses
                        
                        logger.info(f"Set volume to approximately {volume_level}% using key simulation")
                        print(f"Volume set to approximately {volume_level}%")
                        return True
                elif platform.system() == 'Linux':
                    try:
                        # Try using amixer for Linux
                        subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{volume_level}%'], capture_output=True)
                        logger.info(f"Set volume to {volume_level}% on Linux")
                        print(f"Volume set to {volume_level}%")
                        return True
                    except Exception as linux_error:
                        logger.error(f"Error setting volume on Linux: {linux_error}")
                        # Fallback to key simulation
                        # Reset volume first
                        for _ in range(50):
                            pyautogui.press('volumedown')
                        # Increase to target
                        presses = int(volume_level / 2)
                        for _ in range(presses):
                            pyautogui.press('volumeup')
                        logger.info(f"Set volume to approximately {volume_level}% using key simulation")
                        print(f"Volume set to approximately {volume_level}%")
                        return True
                elif platform.system() == 'Darwin':  # macOS
                    try:
                        subprocess.run(['osascript', '-e', f'set volume output volume {volume_level}'], capture_output=True)
                        logger.info(f"Set volume to {volume_level}% on macOS")
                        print(f"Volume set to {volume_level}%")
                        return True
                    except Exception as mac_error:
                        logger.error(f"Error setting volume on macOS: {mac_error}")
                        # Fallback to key simulation as above
                        for _ in range(50):
                            pyautogui.press('volumedown')
                        presses = int(volume_level / 2)
                        for _ in range(presses):
                            pyautogui.press('volumeup')
                        logger.info(f"Set volume to approximately {volume_level}% using key simulation")
                        print(f"Volume set to approximately {volume_level}%")
                        return True
            
            # If we get here, we couldn't handle the command
            logger.warning(f"Unrecognized volume command: {command}")
            print("I couldn't understand the volume command")
            return False
            
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            print("Could not adjust volume")
            return False

    def get_weather(self, location=None):
        """Get current weather information for a location"""
        try:
            print(f"Getting weather information | Category: system_info | Confidence: 0.95")
            
            # Use OpenWeatherMap API (free tier)
            API_KEY = "YOUR_API_KEY"  # User should replace with their own API key
            
            # If no location is provided, attempt to get weather for current location
            if not location:
                try:
                    # Get IP-based location
                    ip_response = requests.get("https://ipinfo.io/json")
                    ip_data = ip_response.json()
                    location = ip_data.get("city", "")
                    if not location:
                        speak("I couldn't determine your location. Please specify a city.")
                        return False
                except Exception as e:
                    logger.error(f"Error getting location from IP: {e}")
                    speak("I couldn't determine your location. Please specify a city.")
                    return False
            
            # Build the API URL
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
            
            # Make the API request
            response = requests.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                weather_data = response.json()
                
                # Extract relevant information
                temp = weather_data["main"]["temp"]
                feels_like = weather_data["main"]["feels_like"]
                humidity = weather_data["main"]["humidity"]
                weather_desc = weather_data["weather"][0]["description"]
                wind_speed = weather_data["wind"]["speed"]
                
                # Get sunrise and sunset times
                sunrise_time = datetime.fromtimestamp(weather_data["sys"]["sunrise"]).strftime("%H:%M")
                sunset_time = datetime.fromtimestamp(weather_data["sys"]["sunset"]).strftime("%H:%M")
                
                # Format the weather information
                weather_info = (
                    f"Weather in {location}: {weather_desc}\n"
                    f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                    f"Humidity: {humidity}%\n"
                    f"Wind Speed: {wind_speed} m/s\n"
                    f"Sunrise: {sunrise_time}, Sunset: {sunset_time}"
                )
                
                print(weather_info)
                speak(f"Current weather in {location} is {weather_desc} with a temperature of {int(temp)} degrees Celsius. "
                      f"Humidity is {humidity} percent.")
                      
                return True
            elif response.status_code == 401:
                logger.error("Invalid API key. Please update your API key in the system_controls.py file.")
                speak("I couldn't access weather data. The API key may be invalid.")
                return False
            elif response.status_code == 404:
                logger.error(f"Location '{location}' not found")
                speak(f"I couldn't find weather information for {location}. Please check the location name.")
                return False
            else:
                logger.error(f"API Error: {response.status_code}")
                speak("I couldn't access weather information at the moment.")
                return False
                
        except Exception as e:
            logger.error(f"Error getting weather information: {e}")
            speak("I'm sorry, but I couldn't retrieve the weather information.")
            return False

    def get_temperature(self):
        """Get detailed CPU and GPU temperature information"""
        try:
            print(f"Command: temperature | Category: system_info | Confidence: 0.95")
            
            if platform.system() == 'Windows':
                try:
                    # Use WMI to get temperature information on Windows
                    w = wmi.WMI(namespace="root\\wmi")
                    temperature_info = w.MSAcpi_ThermalZoneTemperature()
                    
                    # Initialize temperature data dictionary
                    temps = {"CPU": [], "GPU": [], "System": []}
                    gpu_info = ""
                    
                    # Try to get CPU temperature using Open Hardware Monitor if available
                    try:
                        w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                        hardware_temps = w.Sensor()
                        for sensor in hardware_temps:
                            if sensor.SensorType == 'Temperature':
                                if 'cpu' in sensor.Name.lower() or 'core' in sensor.Name.lower():
                                    temps["CPU"].append((sensor.Name, sensor.Value))
                                elif 'gpu' in sensor.Name.lower():
                                    temps["GPU"].append((sensor.Name, sensor.Value))
                                else:
                                    temps["System"].append((sensor.Name, sensor.Value))
                    except Exception:
                        # If Open Hardware Monitor is not available, use MSAcpi
                        for temp_info in temperature_info:
                            # Convert tenths of Kelvin to Celsius
                            temp_celsius = (temp_info.CurrentTemperature / 10.0) - 273.15
                            temps["System"].append(("System", temp_celsius))
                    
                    # Try to get GPU information using nvidia-smi if available
                    try:
                        nvidia_output = subprocess.check_output(
                            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'],
                            universal_newlines=True
                        )
                        for i, temp in enumerate(nvidia_output.strip().split('\n')):
                            temps["GPU"].append((f"NVIDIA GPU {i}", float(temp)))
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # No NVIDIA GPU or nvidia-smi not available
                        pass
                    
                    # Format the temperature information
                    temperature_status = "Temperature Information:\n"
                    
                    # Add CPU temperatures with color coding
                    if temps["CPU"]:
                        temperature_status += "\nCPU Temperatures:\n"
                        for name, temp in temps["CPU"]:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    # Add GPU temperatures with color coding
                    if temps["GPU"]:
                        temperature_status += "\nGPU Temperatures:\n"
                        for name, temp in temps["GPU"]:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    # Add System temperatures with color coding
                    if temps["System"]:
                        temperature_status += "\nSystem Temperatures:\n"
                        for name, temp in temps["System"]:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    if not any(temps.values()):
                        temperature_status = "Temperature information not available. Try installing Open Hardware Monitor for Windows."
                    
                    print(temperature_status)
                    
                    # Log a simplified version
                    log_temps = []
                    for category, temp_list in temps.items():
                        for name, temp in temp_list:
                            log_temps.append(f"{name}: {temp:.1f}°C")
                    
                    if log_temps:
                        logger.info(f"Temperatures: {', '.join(log_temps)}")
                    else:
                        logger.info("No temperature information available")
                    
                    return True
                
                except Exception as e:
                    logger.error(f"Error retrieving Windows temperature information: {e}")
                    print("Temperature information not available")
                    return False
            
            elif platform.system() == 'Linux':
                try:
                    # Check for lm-sensors
                    sensors_output = subprocess.check_output(
                        ['sensors'],
                        universal_newlines=True
                    )
                    
                    # Parse the sensors output
                    cpu_temps = []
                    gpu_temps = []
                    other_temps = []
                    
                    current_device = None
                    for line in sensors_output.split('\n'):
                        if line and not line.startswith(' '):
                            current_device = line.strip(':')
                        elif 'temp' in line.lower() or 'core' in line.lower():
                            if '+' in line and '°C' in line:
                                name_part = line.split(':')[0].strip()
                                temp_part = line.split(':')[1].strip()
                                temp_value = float(temp_part.split()[0].replace('+', '').replace('°C', ''))
                                
                                if 'cpu' in current_device.lower() or 'core' in name_part.lower():
                                    cpu_temps.append((f"{current_device} {name_part}", temp_value))
                                elif 'gpu' in current_device.lower() or 'nvidia' in current_device.lower():
                                    gpu_temps.append((f"{current_device} {name_part}", temp_value))
                                else:
                                    other_temps.append((f"{current_device} {name_part}", temp_value))
                    
                    # Try nvidia-smi for GPU if available
                    try:
                        nvidia_output = subprocess.check_output(
                            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'],
                            universal_newlines=True
                        )
                        for i, temp in enumerate(nvidia_output.strip().split('\n')):
                            gpu_temps.append((f"NVIDIA GPU {i}", float(temp)))
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # No NVIDIA GPU or nvidia-smi not available
                        pass
                    
                    # Format the temperature information
                    temperature_status = "Temperature Information:\n"
                    
                    # Add CPU temperatures with color coding
                    if cpu_temps:
                        temperature_status += "\nCPU Temperatures:\n"
                        for name, temp in cpu_temps:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    # Add GPU temperatures with color coding
                    if gpu_temps:
                        temperature_status += "\nGPU Temperatures:\n"
                        for name, temp in gpu_temps:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    # Add Other temperatures with color coding
                    if other_temps:
                        temperature_status += "\nOther Temperatures:\n"
                        for name, temp in other_temps:
                            color = self._get_temp_color(temp)
                            temperature_status += f"  {name}: {color}{temp:.1f}°C\033[0m\n"
                    
                    if not cpu_temps and not gpu_temps and not other_temps:
                        temperature_status = "No temperature information available. Try installing lm-sensors."
                    
                    print(temperature_status)
                    
                    # Log a simplified version
                    log_temps = []
                    for name, temp in cpu_temps + gpu_temps + other_temps:
                        log_temps.append(f"{name}: {temp:.1f}°C")
                    
                    if log_temps:
                        logger.info(f"Temperatures: {', '.join(log_temps)}")
                    else:
                        logger.info("No temperature information available")
                    
                    return True
                
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Alternative method: check thermal zones
                    try:
                        thermal_zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')
                        if thermal_zones:
                            temperature_status = "Temperature Information:\n\nThermal Zones:\n"
                            log_temps = []
                            
                            for zone_path in thermal_zones:
                                zone_name = zone_path.split('/')[-2]
                                with open(zone_path, 'r') as f:
                                    # Convert millidegrees Celsius to degrees Celsius
                                    temp = float(f.read().strip()) / 1000.0
                                
                                color = self._get_temp_color(temp)
                                temperature_status += f"  {zone_name}: {color}{temp:.1f}°C\033[0m\n"
                                log_temps.append(f"{zone_name}: {temp:.1f}°C")
                            
                            print(temperature_status)
                            logger.info(f"Temperatures: {', '.join(log_temps)}")
                            return True
                        else:
                            print("No temperature information available. Try installing lm-sensors.")
                            logger.info("No temperature information available")
                            return False
                    
                    except Exception as e:
                        logger.error(f"Error retrieving Linux temperature information: {e}")
                        print("Temperature information not available")
                        return False
            
            elif platform.system() == 'Darwin':  # macOS
                try:
                    # Use osx-cpu-temp or iStats if available
                    try:
                        temp_output = subprocess.check_output(
                            ['osx-cpu-temp'],
                            universal_newlines=True
                        )
                        
                        # Extract the temperature value
                        temp_match = re.search(r'(\d+\.\d+).*C', temp_output)
                        if temp_match:
                            temp = float(temp_match.group(1))
                            color = self._get_temp_color(temp)
                            
                            temperature_status = f"CPU Temperature: {color}{temp:.1f}°C\033[0m"
                            print(temperature_status)
                            logger.info(f"CPU Temperature: {temp:.1f}°C")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # Try iStats
                        try:
                            temp_output = subprocess.check_output(
                                ['istats'],
                                universal_newlines=True
                            )
                            
                            # Parse istats output
                            temperatures = []
                            for line in temp_output.split('\n'):
                                if '°C' in line:
                                    parts = line.split(':')
                                    if len(parts) >= 2:
                                        name = parts[0].strip()
                                        temp_match = re.search(r'(\d+\.\d+).*C', parts[1])
                                        if temp_match:
                                            temp = float(temp_match.group(1))
                                            temperatures.append((name, temp))
                            
                            if temperatures:
                                temperature_status = "Temperature Information:\n"
                                log_temps = []
                                
                                for name, temp in temperatures:
                                    color = self._get_temp_color(temp)
                                    temperature_status += f"{name}: {color}{temp:.1f}°C\033[0m\n"
                                    log_temps.append(f"{name}: {temp:.1f}°C")
                                
                                print(temperature_status)
                                logger.info(f"Temperatures: {', '.join(log_temps)}")
                                return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            # Neither tool is available
                            print("No temperature information available. Try installing osx-cpu-temp or istats.")
                            logger.info("No temperature information available")
                            return False
                
                except Exception as e:
                    logger.error(f"Error retrieving macOS temperature information: {e}")
                    print("Temperature information not available")
                    return False
            
            else:
                print(f"Temperature monitoring not supported on {platform.system()}")
                return False
        
        except Exception as e:
            logger.error(f"Error getting temperature information: {e}")
            print("Could not retrieve temperature information")
            return False
    
    def _get_temp_color(self, temp):
        """Return ANSI color code based on temperature value in Celsius"""
        if temp < 60:
            return "\033[92m"  # Green for normal (below 60°C)
        elif temp < 80:
            return "\033[93m"  # Yellow for warm (60-80°C)
        else:
            return "\033[91m"  # Red for hot (above 80°C)

    def control_system(self, command):
        """Control system functions based on command"""
        try:
            command = command.lower()
            
            # Application commands
            if any(word in command for word in ["open", "launch", "start", "run"]):
                # Extract app name from command
                app_name = self.extract_app_name(command)
                if app_name:
                    logger.info(f"Extracted app name: '{app_name}' from command: '{command}'")
                    return self.launch_application(command)
            
            # Window management commands
            elif "minimize" in command:
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.control_window(command)
            elif "maximize" in command:
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.control_window(command)
            elif "close" in command:
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.control_window(command)
            
            # System power commands
            elif any(phrase in command for phrase in ["shutdown", "turn off computer", "shut down computer"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.system_power_control(command)
            elif any(phrase in command for phrase in ["restart", "reboot"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.system_power_control(command)
            elif any(phrase in command for phrase in ["log off", "sign out"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.system_power_control(command)
            elif any(phrase in command for phrase in ["lock computer", "lock system", "lock screen"]):
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.system_power_control(command)
            
            # Volume control commands
            elif "volume" in command:
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.adjust_volume(command)
            
            # Brightness control commands
            elif "brightness" in command:
                print(f"Command: {command} | Category: system_control | Confidence: 0.95")
                return self.adjust_brightness(command)
            
            # System information commands
            elif any(word in command for word in ["cpu", "memory", "ram", "disk", "drive", "system info", "temperature"]):
                return self.get_system_info(command)
            
            # Take screenshot command
            elif "screenshot" in command:
                return self.take_screenshot()
            
            # Weather command
            elif "weather" in command:
                return self.get_weather()
            
            # Unknown command
            else:
                logger.warning(f"Unknown system control command: {command}")
                print(f"I don't know how to execute: {command}")
                return False
                
        except Exception as e:
            logger.error(f"Error in system control: {e}")
            print(f"Error executing command: {command}")
            return False

# For backward compatibility
def control_system(command):
    """Wrapper function for backward compatibility"""
    system_controls = SystemControls()
    return system_controls.control_system(command)
