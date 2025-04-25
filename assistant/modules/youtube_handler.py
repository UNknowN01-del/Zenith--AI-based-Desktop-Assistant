import webbrowser
import re
import logging
import requests
from bs4 import BeautifulSoup
import time
import pyautogui
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeHandler:
    """Handle YouTube video search and playback functionality"""
    
    def __init__(self, api_key=None):
        """
        Initialize YouTubeHandler instance
        
        Args:
            api_key (str, optional): YouTube API key for enhanced video search
        """
        self.api_key = api_key
        self.last_video_url = None
        self.current_video = None
        self.video_state = None
        
        # YouTube direct URL formats
        self.youtube_url = "https://www.youtube.com"
        self.youtube_search_url = "https://www.youtube.com/results?search_query="
        self.youtube_watch_url = "https://www.youtube.com/watch?v="
        
        print("YouTubeHandler initialized successfully")
    
    def search_and_play(self, search_query, index=0):
        """
        Search for a YouTube video and play it
        
        Args:
            search_query (str): The search query
            index (int, optional): The index of the video to play. Defaults to 0.
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not search_query or not isinstance(search_query, str):
                print("Invalid YouTube search query")
                return False
            
            # Clean up the search query
            search_query = search_query.strip()
            
            print(f"Playing YouTube video for: {search_query} (index: {index})")
            
            # Try to get the video URL
            video_url = self.get_youtube_video_url(search_query, index)
            
            if video_url:
                print(f"Playing YouTube video: {video_url}")
                # Open the video URL directly for playback
                webbrowser.open(video_url)
                # Store video information
                self.last_video_url = video_url
                self.current_video = self.get_video_info(video_url)
                self.video_state = 'playing'
                
                # Give the browser time to load
                time.sleep(2)
                
                # Try to ensure video playback starts by sending a keyboard space press
                # This works in most browsers to start video playback
                try:
                    pyautogui.press('space')
                    time.sleep(0.5)
                    # If we're in fullscreen mode, press space again (sometimes needed)
                    pyautogui.press('space')
                except Exception as keypress_error:
                    logger.warning(f"Could not send play keypress: {str(keypress_error)}")
                
                return True
            else:
                # Fallback to direct video search
                encoded_query = urllib.parse.quote_plus(search_query)
                # Use the video URL that automatically plays the first result
                direct_play_url = f"{self.youtube_search_url}{encoded_query}&sp=EgIQAQ%253D%253D"
                print(f"Opening YouTube direct play search: {direct_play_url}")
                webbrowser.open(direct_play_url)
                
                # Give the browser time to load
                time.sleep(2)
                
                # Try to ensure video playback starts
                try:
                    pyautogui.press('space')
                except Exception as keypress_error:
                    logger.warning(f"Could not send play keypress: {str(keypress_error)}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error in YouTube search and play: {str(e)}")
            print(f"Failed to search YouTube: {str(e)}")
            return False
    
    def get_youtube_video_url(self, search_query, video_index=0):
        """
        Get the video URL from YouTube search results based on index
        
        Args:
            search_query (str): The search query
            video_index (int, optional): The index of the video to retrieve. Defaults to 0.
            
        Returns:
            str: The video URL or None if not found
        """
        try:
            # Validate input
            if not search_query:
                return None
                
            # Ensure video_index is a valid integer
            try:
                video_index = int(video_index)
            except (ValueError, TypeError):
                video_index = 0
                
            # Clean up the search query
            search_query = re.sub(r'[^\w\s]', '', search_query)
            search_query = re.sub(r'\s+', '+', search_query)
            
            # Create search URL
            search_url = f"{self.youtube_search_url}{search_query}"
            
            # Send request to get search results
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try up to 3 methods to get video URL
            for attempt in range(3):
                try:
                    response = requests.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Different extraction methods
                        if attempt == 0:
                            # Method 1: Extract video IDs using regex
                            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
                            
                            # Remove duplicates while preserving order
                            unique_video_ids = []
                            for video_id in video_ids:
                                if video_id not in unique_video_ids:
                                    unique_video_ids.append(video_id)
                            
                            if unique_video_ids and len(unique_video_ids) > video_index:
                                video_url = f"{self.youtube_watch_url}{unique_video_ids[video_index]}"
                                return video_url
                                
                        elif attempt == 1:
                            # Method 2: Parse HTML with BeautifulSoup
                            soup = BeautifulSoup(response.text, 'html.parser')
                            video_elements = soup.find_all('a', href=re.compile(r'/watch\?v='))
                            
                            if video_elements and len(video_elements) > video_index:
                                href = video_elements[video_index]['href']
                                if href.startswith('/watch'):
                                    video_url = f"{self.youtube_url}{href}"
                                    return video_url
                                    
                        else:
                            # Method 3: Look for videoId in the JSON data
                            video_id_pattern = r'"videoId":"([^"]+)"'
                            video_ids_json = re.findall(video_id_pattern, response.text)
                            
                            if video_ids_json and len(video_ids_json) > video_index:
                                video_url = f"{self.youtube_watch_url}{video_ids_json[video_index]}"
                                return video_url
                                
                except requests.exceptions.RequestException as req_e:
                    logger.error(f"Request error in method {attempt+1}: {str(req_e)}")
                    continue
                except Exception as inner_e:
                    logger.error(f"Method {attempt+1} failed: {str(inner_e)}")
                    continue
                
            # Fallback: just return the search URL
            return None
                
        except Exception as e:
            logger.error(f"Error getting video URL: {str(e)}")
        
        return None
    
    def get_video_info(self, video_url):
        """
        Get information about a YouTube video
        
        Args:
            video_url (str): The video URL
            
        Returns:
            dict: Video information or None if not found
        """
        try:
            if not video_url:
                return None
                
            # Extract video ID
            video_id = re.search(r'watch\?v=(\S{11})', video_url)
            if not video_id:
                return None
                
            video_id = video_id.group(1)
            
            # Get video info
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                response = requests.get(video_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to get title
                    title = None
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.text.replace(' - YouTube', '')
                    
                    return {
                        'id': video_id,
                        'url': video_url,
                        'title': title
                    }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error in get_video_info: {str(e)}")
                # Return minimal info with just the ID
                return {
                    'id': video_id,
                    'url': video_url,
                    'title': None
                }
                
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
        return None
    
    def extract_video_index(self, command):
        """
        Extract video index from command (e.g., 'first', 'second', '1st', '2nd', etc.)
        
        Args:
            command (str): The command to process
            
        Returns:
            int: The extracted video index (0-based)
        """
        if not command or not isinstance(command, str):
            return 0
            
        command = command.lower()
        
        # Dictionary mapping words to numbers
        number_words = {
            'first': 0, '1st': 0,
            'second': 1, '2nd': 1,
            'third': 2, '3rd': 2,
            'fourth': 3, '4th': 3,
            'fifth': 4, '5th': 4,
            'sixth': 5, '6th': 5,
            'seventh': 6, '7th': 6,
            'eighth': 7, '8th': 7,
            'ninth': 8, '9th': 8,
            'tenth': 9, '10th': 9,
            'one': 0, 'two': 1, 'three': 2, 'four': 3, 'five': 4,
            'six': 5, 'seven': 6, 'eight': 7, 'nine': 8, 'ten': 9
        }
        
        # First check for specific phrases like "play the second video"
        index_pattern = r'(?:play|open|show)\s+(?:the\s+)?(\w+)(?:\s+video|\s+result)'
        match = re.search(index_pattern, command, re.IGNORECASE)
        if match:
            index_word = match.group(1).lower()
            if index_word in number_words:
                return number_words[index_word]
        
        # Look for number words in the command
        for word, index in number_words.items():
            if word in command.split():
                return index
                
        # Look for numeric values
        numbers = re.findall(r'\b\d+\b', command)
        if numbers:
            try:
                num = int(numbers[0])
                # Ensure 1-based user numbering is converted to 0-based index
                return max(0, num - 1)  # Convert to 0-based index, ensure it's at least 0
            except ValueError:
                pass
            
        return 0  # Default to first video
    
    def extract_search_query(self, command):
        """
        Extract the search query from a YouTube command
        
        Args:
            command (str): The command to process
            
        Returns:
            str: The extracted search query or None if not found
        """
        if not command or not isinstance(command, str):
            return None
            
        command = command.lower()
        
        # Handle compound commands like "open YouTube and play..."
        if "and play" in command:
            parts = command.split("and play")
            if len(parts) > 1:
                command = "play " + parts[1].strip()
        
        # Check for YouTube-specific commands
        youtube_patterns = [
            r"(?:play|search for|find|watch)\s+(.+?)(?:\s+on youtube|\s+in youtube|$)",
            r"youtube\s+(?:search|find|play|watch)\s+(?:for\s+)?(.+)",
            r"(?:search|find|play|watch)\s+(?:youtube|video)\s+(?:for\s+)?(.+)",
            r"(?:play|find|search|show)\s+(?:me\s+)?(.+?)(?:\s+video|\s+song|\s+music|\s+playlist)?(?:\s+on youtube)?$",
            r"(?:search|find)\s+for\s+(.+?)(?:\s+on youtube|\s+in youtube|$)",
            r"(?:show|get)\s+(?:me\s+)?(.+?)(?:\s+video|\s+on youtube)?$"
        ]
        
        # Try each pattern
        for pattern in youtube_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                # Clean up the query by removing YouTube-related terms
                query = re.sub(r"\b(?:on|in)\s+youtube\b", "", query, flags=re.IGNORECASE).strip()
                query = re.sub(r"\bvideo(?:s)?\b", "", query, flags=re.IGNORECASE).strip()
                
                # Remove phrases like "the first" or "the second" from the query
                query = re.sub(r"\b(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+", "", query, flags=re.IGNORECASE).strip()
                
                # If query is too short or empty after cleaning, return None
                if len(query) < 2:
                    continue
                    
                return query
        
        # If no specific pattern matches, get the relevant part after key phrases
        key_phrases = ["play", "search for", "find", "watch", "youtube", "video of", "search", "look for"]
        for phrase in key_phrases:
            if phrase in command:
                parts = command.split(phrase, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                    # Only use if substantial content remains
                    if len(query) > 2:
                        # Clean up additional terms
                        query = re.sub(r"\b(?:on|in)\s+youtube\b", "", query, flags=re.IGNORECASE).strip()
                        query = re.sub(r"\bvideo(?:s)?\b", "", query, flags=re.IGNORECASE).strip()
                        return query
                        
        # Check if the command itself is a viable search query (e.g., just "beethoven symphony")
        if len(command) > 3 and " " in command:
            # Check if the command doesn't start with common YouTube action verbs
            action_verbs = ["play", "search", "find", "watch", "open", "get", "show", "look"]
            if not any(command.startswith(verb) for verb in action_verbs):
                return command
                
        # If all else fails, use the original command if it's reasonable
        if len(command) > 3 and not any(x in command for x in ["youtube", "play", "search", "find", "watch"]):
            return command
            
        return None
    
    def control_playback(self, action):
        """
        Control YouTube video playback
        
        Args:
            action (str): Action to perform (play, pause, stop, next, previous, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not action or not isinstance(action, str):
                return False
                
            action = action.lower().strip()
            print(f"Controlling YouTube playback: {action}")
            
            # If command starts with "play" and has more words, it's likely a search
            if action.startswith("play") and len(action.split()) > 1:
                # Extract the search query (everything after "play")
                search_parts = action.split(" ", 1)
                if len(search_parts) > 1:
                    search_query = search_parts[1].strip()
                    # If it still has "youtube" in it, remove that
                    search_query = search_query.replace("youtube", "").replace("on", "").strip()
                    if search_query:
                        print(f"Redirecting to search_and_play: {search_query}")
                        return self.search_and_play(search_query)
                
            # Handle actions
            if action in ['pause', 'play', 'toggle', 'play/pause']:
                # Press space to toggle play/pause
                pyautogui.press('space')
                self.video_state = 'paused' if self.video_state == 'playing' else 'playing'
                print(f"YouTube video {self.video_state}")
                return True
                
            elif action == 'stop':
                # Press 'k' to pause and then reload page to stop
                pyautogui.press('k')
                pyautogui.hotkey('ctrl', 'r')
                self.video_state = None
                print("YouTube video stopped")
                return True
                
            elif action in ['skip', 'next', 'forward']:
                # Press 'l' to skip forward
                pyautogui.press('l')
                print("Skipped forward in YouTube video")
                return True
                
            elif action in ['back', 'previous', 'rewind', 'backward']:
                # Press 'j' to skip backward
                pyautogui.press('j')
                print("Skipped backward in YouTube video")
                return True
                
            elif action == 'fullscreen' or action == 'full screen':
                # Press 'f' to toggle fullscreen
                pyautogui.press('f')
                print("Toggled fullscreen mode")
                return True
                
            elif action == 'mute' or action == 'unmute':
                # Press 'm' to toggle mute
                pyautogui.press('m')
                print("Toggled mute")
                return True
                
            elif action == 'captions' or action == 'subtitles':
                # Press 'c' to toggle captions
                pyautogui.press('c')
                print("Toggled captions")
                return True
                
            # Handle volume control
            volume_up_match = re.search(r'volume\s+up|increase\s+volume', action)
            volume_down_match = re.search(r'volume\s+down|decrease\s+volume|lower\s+volume', action)
            
            if volume_up_match:
                # Press up arrow to increase volume
                pyautogui.press('up')
                print("Increased YouTube volume")
                return True
                
            elif volume_down_match:
                # Press down arrow to decrease volume
                pyautogui.press('down')
                print("Decreased YouTube volume")
                return True
                
            # Handle seeking
            seek_forward_match = re.search(r'(?:seek|go|skip)\s+forward|(?:seek|go|skip)\s+ahead', action)
            seek_backward_match = re.search(r'(?:seek|go|skip)\s+backward|(?:seek|go|skip)\s+back', action)
            
            if seek_forward_match:
                # Press right arrow to seek forward
                pyautogui.press('right')
                print("Sought forward in YouTube video")
                return True
                
            elif seek_backward_match:
                # Press left arrow to seek backward
                pyautogui.press('left')
                print("Sought backward in YouTube video")
                return True
                
            print(f"Unknown YouTube playback action: {action}")
            return False
            
        except Exception as e:
            logger.error(f"Error controlling YouTube playback: {str(e)}")
            print(f"Failed to control YouTube playback: {str(e)}")
            return False
            
    def open_youtube_main(self):
        """Open the YouTube main page"""
        try:
            print("Opening YouTube main page")
            webbrowser.open(self.youtube_url)
            return True
        except Exception as e:
            logger.error(f"Error opening YouTube main page: {str(e)}")
            print(f"Failed to open YouTube main page: {str(e)}")
            return False