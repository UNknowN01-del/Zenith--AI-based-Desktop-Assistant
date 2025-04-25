#!/usr/bin/env python
import webbrowser
import re
import logging
import requests
import json
from bs4 import BeautifulSoup
import os
import random
from assistant.modules.speech_utils import speak
import time
import pyautogui
import keyboard
import urllib.parse
import subprocess
from typing import Optional, List, Dict, Any, Union
from assistant.modules.youtube_handler import YouTubeHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearch:
    """Handle web search and YouTube playback functionality"""
    
    def __init__(self):
        """Initialize WebSearch instance"""
        # Initialize search engines
        self.search_engines = {
            'google': 'https://www.google.com/search?q=',
            'bing': 'https://www.bing.com/search?q=',
            'duckduckgo': 'https://duckduckgo.com/?q=',
            'youtube': 'https://www.youtube.com/results?search_query='
        }
        
        # Initialize news sources
        self.news_sources = {
            'cnn': 'https://www.cnn.com',
            'bbc': 'https://www.bbc.com/news',
            'foxnews': 'https://www.foxnews.com',
            'reuters': 'https://www.reuters.com',
            'bloomberg': 'https://www.bloomberg.com',
            'wsj': 'https://www.wsj.com',
            'nytimes': 'https://www.nytimes.com',
            'washingtonpost': 'https://www.washingtonpost.com',
            'guardian': 'https://www.theguardian.com',
            'cnbc': 'https://www.cnbc.com'
        }
        
        # Initialize YouTube handler
        self.youtube_handler = YouTubeHandler()
        
        # Store search history
        self.search_history = []
        
        print("WebSearch initialized successfully")
    
    def search_web(self, command):
        """
        Search the web based on command
        
        Args:
            command (str): The command to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input
            if not command or not isinstance(command, str):
                print("Empty or invalid search command")
                return False
                
            command = command.strip()
            
            # Log the command
            logger.info(f"Processing web search: {command}")
            
            # Handle YouTube commands with higher priority
            if self._is_youtube_command(command):
                return self.handle_youtube_command(command)
                
            # Handle direct website commands
            direct_site_match = re.search(r'(?:open|go\s+to|launch|visit|browse|navigate\s+to)\s+(?:the\s+)?(\w+)(?:\.com|\s+website|\s+site)?', command, re.IGNORECASE)
            if direct_site_match:
                site = direct_site_match.group(1).lower()
                
                # Check if it's a news site
                if site in self.news_sources:
                    print(f"Opening {site} news website")
                    webbrowser.open(self.news_sources[site])
                    return True
                
                # Check for common websites
                common_sites = {
                    'google': 'https://www.google.com',
                    'facebook': 'https://www.facebook.com',
                    'twitter': 'https://www.twitter.com',
                    'x': 'https://x.com',
                    'instagram': 'https://www.instagram.com',
                    'reddit': 'https://www.reddit.com',
                    'amazon': 'https://www.amazon.com',
                    'youtube': 'https://www.youtube.com',
                    'linkedin': 'https://www.linkedin.com',
                    'github': 'https://www.github.com',
                    'stackoverflow': 'https://www.stackoverflow.com',
                    'netflix': 'https://www.netflix.com',
                    'gmail': 'https://mail.google.com',
                    'outlook': 'https://outlook.live.com',
                    'yahoo': 'https://www.yahoo.com',
                    'wikipedia': 'https://www.wikipedia.org',
                    'pinterest': 'https://www.pinterest.com',
                    'quora': 'https://www.quora.com',
                    'spotify': 'https://www.spotify.com',
                    'twitch': 'https://www.twitch.tv',
                    'dropbox': 'https://www.dropbox.com',
                    'microsoft': 'https://www.microsoft.com',
                    'apple': 'https://www.apple.com',
                    'ebay': 'https://www.ebay.com'
                }
                
                if site in common_sites:
                    print(f"Opening {site} website")
                    webbrowser.open(common_sites[site])
                    return True
                
                # Try to open with .com extension if not found
                print(f"Opening {site}.com")
                webbrowser.open(f"https://www.{site}.com")
                return True
            
            # Extract search query and search engine
            search_query = self._extract_search_query(command)
            search_engine = self._extract_search_engine(command)
            
            # Use default search engine if not specified
            if not search_engine:
                search_engine = 'google'
                
            # Handle news commands
            if re.search(r'\b(?:news|headlines|latest|current events)\b', command, re.IGNORECASE):
                # Extract news source if specified
                news_source_match = re.search(r'(?:from|on)\s+(?:the\s+)?(\w+)(?:\s+news)?', command, re.IGNORECASE)
                
                if news_source_match:
                    source = news_source_match.group(1).lower()
                    if source in self.news_sources:
                        print(f"Opening {source} news")
                        webbrowser.open(self.news_sources[source])
                        return True
                        
                # If no specific source or source not found, do a news search
                if search_query:
                    print(f"Searching for {search_query} news")
                    webbrowser.open(f"{self.search_engines['google']}news+{urllib.parse.quote_plus(search_query)}")
                    return True
                else:
                    # Open Google News if no specific query
                    print("Opening Google News")
                    webbrowser.open("https://news.google.com")
                    return True
            
            # Perform the search
            if search_query:
                print(f"Searching the web for: {search_query} (using {search_engine})")
                
                # Clean up the search query (remove search engine mentions, etc.)
                search_query = re.sub(r'\b(?:on|using|with|via)\s+(?:google|bing|duckduckgo|youtube)\b', '', search_query, flags=re.IGNORECASE).strip()
                
                # Clean up "search for" and similar phrases
                search_query = re.sub(r'\b(?:search|look|find)\s+(?:for|about|up)?\b', '', search_query, flags=re.IGNORECASE).strip()
                
                # Encode the search query
                encoded_query = urllib.parse.quote_plus(search_query)
                
                # Construct the search URL
                search_url = f"{self.search_engines[search_engine]}{encoded_query}"
                
                # Add to search history
                self.search_history.append({'query': search_query, 'engine': search_engine, 'timestamp': time.time()})
                
                # Open the search URL
                webbrowser.open(search_url)
                return True
            else:
                # Open the search engine's homepage if no specific query
                print(f"Opening {search_engine} homepage")
                webbrowser.open(self.search_engines[search_engine].split('?')[0])
                return True
                
        except Exception as e:
            logger.error(f"Error searching the web: {str(e)}")
            print(f"Failed to search the web: {str(e)}")
            return False
            
    def _is_youtube_command(self, command):
        """
        Check if the command is related to YouTube
        
        Args:
            command (str): The command to check
            
        Returns:
            bool: True if YouTube-related, False otherwise
        """
        if not command:
            return False
            
        command = command.lower()
        
        # Check for direct YouTube commands
        if re.search(r'\b(?:open|launch|start)\s+(?:the\s+)?youtube\b', command, re.IGNORECASE):
            return True
            
        # Check for YouTube search or play commands
        if re.search(r'\b(?:youtube|watch)\b', command, re.IGNORECASE):
            return True
            
        # Check for video playback commands
        if re.search(r'\b(?:play|search|find|watch)\s+(?:for\s+)?(?:a\s+)?(?:video|song|music)\b', command, re.IGNORECASE):
            return True
            
        # Check for playback control commands if already in YouTube
        playback_actions = ['play', 'pause', 'stop', 'next', 'previous', 'skip', 'forward', 'back', 
                          'rewind', 'fullscreen', 'mute', 'unmute', 'volume up', 'volume down', 
                          'increase volume', 'decrease volume', 'captions', 'subtitles']
        
        if any(action in command for action in playback_actions):
            # Only return True if we detect it's a pure media control command
            # without other context that would make it a general search
            if not re.search(r'\b(?:search|find|look|google|bing)\b', command, re.IGNORECASE):
                return True
                
        return False
        
    def handle_youtube_command(self, command):
        """
        Handle YouTube-specific commands
        
        Args:
            command (str): The command to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            command = command.lower()
            
            # Direct YouTube open command
            if re.match(r'\b(?:open|launch|start|go\s+to)\s+(?:the\s+)?youtube\b', command, re.IGNORECASE):
                return self.youtube_handler.open_youtube_main()
                
            # Check explicitly if this is a search command
            is_search_command = re.search(r'\b(?:search|find|look)\b', command, re.IGNORECASE) is not None
            is_play_command = re.search(r'\b(?:play|watch)\b', command, re.IGNORECASE) is not None
                
            # Extract potential playback control command
            playback_actions = ['play', 'pause', 'stop', 'next', 'previous', 'skip', 'forward', 'back', 
                             'rewind', 'fullscreen', 'mute', 'unmute', 'volume up', 'volume down', 
                             'increase volume', 'decrease volume', 'captions', 'subtitles',
                             'seek forward', 'seek backward']
            
            # Check if it's a pure playback control command (not search/play)
            is_simple_playback_control = any(command == action for action in playback_actions)
            
            if is_simple_playback_control:
                # For simple playback commands like "pause", "play", etc.
                return self.youtube_handler.control_playback(command)
                
            # Extract the search query and video index
            search_query = self.youtube_handler.extract_search_query(command)
            video_index = self.youtube_handler.extract_video_index(command)
            
            # If we have a search query
            if search_query:
                if is_search_command and not is_play_command:
                    # If this is explicitly a search command, just search without playing
                    print(f"Searching YouTube for: {search_query}")
                    webbrowser.open(f"{self.search_engines['youtube']}{urllib.parse.quote_plus(search_query)}")
                    return True
                elif is_play_command:
                    # If this is explicitly a play command, search and play
                    return self.youtube_handler.search_and_play(search_query, video_index)
                else:
                    # If no explicit search or play keyword, just search
                    print(f"Searching YouTube for: {search_query}")
                    webbrowser.open(f"{self.search_engines['youtube']}{urllib.parse.quote_plus(search_query)}")
                    return True
            else:
                # If no search query but YouTube is mentioned, just open YouTube
                return self.youtube_handler.open_youtube_main()
                
        except Exception as e:
            logger.error(f"Error handling YouTube command: {str(e)}")
            print(f"Failed to handle YouTube command: {str(e)}")
            return False
            
    def _extract_search_query(self, command):
        """
        Extract the search query from a command
        
        Args:
            command (str): The command to process
            
        Returns:
            str: The extracted search query or None if not found
        """
        if not command:
            return None
            
        command = command.lower().strip()
        
        # First, check for common search patterns
        search_patterns = [
            r"(?:search|look|find)(?:\s+for)?(?:\s+about)?\s+(.+?)(?:\s+on|using|with|via)?\s+(?:google|bing|duckduckgo|youtube)?$",
            r"(?:google|bing|duckduckgo)\s+(?:for|about)?\s+(.+)",
            r"(?:find|get|show)(?:\s+me)?\s+(?:information|info|details)\s+(?:about|on)\s+(.+)",
            r"(?:search|look|find)(?:\s+for)?(?:\s+about)?\s+(.+)",
            r"(?:how\s+to|what\s+is|who\s+is|where\s+is|when\s+is|why\s+is)\s+(.+)"
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        # If no specific pattern matches, try to extract after search keywords
        search_keywords = ["search", "look", "find", "google", "bing", "duckduckgo", "information about", "details on"]
        for keyword in search_keywords:
            if keyword in command:
                parts = command.split(keyword, 1)
                if len(parts) > 1:
                    query = parts[1].strip()
                    if query:
                        return query
                        
        # Check if it's just a "how to" or "what is" question without the search keywords
        question_match = re.match(r'^(?:how|what|who|where|when|why|is|are|can|do|does|did|will|should|would)(.+)', command, re.IGNORECASE)
        if question_match:
            return command
            
        # If all else fails and it's not a control command, use the original command
        control_keywords = ["open", "launch", "close", "exit", "stop", "play", "pause", "volume", "brightness", "screenshot"]
        if not any(keyword in command for keyword in control_keywords):
            return command
            
        return None
        
    def _extract_search_engine(self, command):
        """
        Extract the search engine from a command
        
        Args:
            command (str): The command to process
            
        Returns:
            str: The extracted search engine or None if not found
        """
        if not command:
            return None
            
        command = command.lower()
        
        # Check for explicit search engine mentions
        engine_match = re.search(r'(?:on|using|with|via)\s+(?:the\s+)?(\w+)', command, re.IGNORECASE)
        if engine_match:
            engine = engine_match.group(1).lower()
            if engine in self.search_engines:
                return engine
            elif engine in ['google', 'bing', 'duckduckgo', 'youtube']:
                return engine
                
        # Check for search engine mentioned at the beginning of the command
        for engine in self.search_engines:
            if command.startswith(engine):
                return engine
                
        # No search engine specified, use default
        return None
        
    def get_news(self, source=None):
        """
        Get news from a specified source or open a general news site
        
        Args:
            source (str, optional): The news source to use. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if source and source.lower() in self.news_sources:
                print(f"Opening {source} news")
                webbrowser.open(self.news_sources[source.lower()])
                return True
            else:
                # If no source specified or source not found, use Google News
                print("Opening Google News")
                webbrowser.open("https://news.google.com")
                return True
                
        except Exception as e:
            logger.error(f"Error getting news: {str(e)}")
            print(f"Failed to get news: {str(e)}")
            return False
    
    def get_search_history(self):
        """
        Get the search history
        
        Returns:
            list: List of previous searches
        """
        return self.search_history
    
    def control_video_playback(self, action):
        """
        Control video playback (play, pause, stop)
        
        Args:
            action (str): The action to perform (play, pause, stop)
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Video control: {action}")
        # Delegate to the YouTube handler
        return self.youtube_handler.control_playback(action)
    
    def clear_search_history(self):
        """
        Clear the search history
        
        Returns:
            bool: True if successful
        """
        self.search_history = []
        print("Search history cleared")
        return True

    def search_youtube(self, query):
        """
        Search YouTube for a given query and open the results page.

        Args:
            query (str): The search query for YouTube.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not query or not isinstance(query, str):
                print("Empty or invalid YouTube search query")
                return False

            # Clean up the query
            query = query.strip()

            # Log the query
            logger.info(f"Searching YouTube for: {query}")

            # Encode the query
            encoded_query = urllib.parse.quote_plus(query)

            # Construct the YouTube search URL
            youtube_search_url = f"{self.search_engines['youtube']}{encoded_query}"

            # Open the YouTube search URL
            webbrowser.open(youtube_search_url)
            return True
        except Exception as e:
            logger.error(f"Error searching YouTube: {str(e)}")
            print(f"Failed to search YouTube: {str(e)}")
            return False

    def play_youtube_video(self, query):
        """
        Play a YouTube video based on a search query.

        Args:
            query (str): The search query for the YouTube video.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not query or not isinstance(query, str):
                print("Empty or invalid YouTube video query")
                return False

            # Clean up the query
            query = query.strip()

            # Log the query
            logger.info(f"Playing YouTube video for: {query}")

            # Directly use the YouTube handler for playing videos
            return self.youtube_handler.search_and_play(query, 0)
            
        except Exception as e:
            logger.error(f"Error playing YouTube video: {str(e)}")
            print(f"Failed to play YouTube video: {str(e)}")
            return False
