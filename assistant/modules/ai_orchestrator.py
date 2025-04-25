#!/usr/bin/env python
"""
AI Orchestrator for managing all AI features seamlessly
"""
import threading
from queue import Queue
import logging
from typing import Dict, Any, Optional, List, Tuple
from .huggingface_utils import HuggingFaceHelper
from .nlp_learning import CommandLearner
import os
import json
from datetime import datetime
from .config_handler import config
import random
import re
import spacy
import nltk
import psutil
import platform
import subprocess

# Import modules
from .system_controls import SystemControls
from .media_controls import MediaControls
from .web_search import WebSearch
from .speech_utils import speak
from .config_handler import ConfigHandler

logger = logging.getLogger(__name__)

class AIOrchestratorSingleton:
    """Singleton AI Orchestrator to coordinate various modules"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = AIOrchestrator()
        return cls._instance

class AIOrchestrator:
    def __init__(self):
        """Initialize the AI Orchestrator"""
        self.command_learner = CommandLearner()
        self.categories = [
            "web_search",
            "system_control",
            "media_control",
            "system_info",
            "screenshot",
            "youtube_search",
            "youtube_play",
            "video_control"
        ]
        self.system_controls = SystemControls()
        self.media_controls = MediaControls()
        self.web_search = WebSearch()
        self.config_handler = ConfigHandler()
        self.config = self.config_handler.config
        
        # Initialize modules status
        self.modules_status = {
            "system_controls": True,
            "media_controls": True,
            "web_search": True
        }
        
        logger.info("AI Orchestrator initialized successfully")
    
    def preprocess_command(self, command_text):
        """Preprocess and categorize a command"""
        try:
            if not command_text:
                return {
                    "command": "",
                    "category": "web_search",
                    "confidence": 0.0
                }
            
            # Clean and normalize the command
            command = command_text.strip().lower()
            
            # Check for YouTube commands first
            if any(word in command for word in ["youtube", "video", "play", "watch"]):
                if "search" in command or "find" in command:
                    return {
                        "command": command,
                        "category": "youtube_search",
                        "confidence": 0.9
                    }
                elif "play" in command:
                    return {
                        "command": command,
                        "category": "youtube_play",
                        "confidence": 0.9
                    }
            
            # Check for screenshot commands
            if any(word in command for word in ["screenshot", "capture screen", "grab screen"]):
                return {
                    "command": command,
                    "category": "screenshot",
                    "confidence": 0.9
                }
            
            # Get category predictions
            category, confidence = self.command_learner.predict_category(command)
            
            return {
                "command": command,
                "category": category,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error in command preprocessing: {e}")
            return {
                "command": command_text,
                "category": "web_search",
                "confidence": 0.3
            }
    
    def enhance_command(self, command, category):
        """Enhance a command with additional context"""
        try:
            # Add category-specific enhancements
            if category == "web_search":
                return f"search for {command}"
            elif category == "youtube_search":
                return f"search youtube for {command}"
            elif category == "youtube_play":
                return f"play {command} on youtube"
            else:
                return command
        except Exception as e:
            logger.error(f"Error enhancing command: {e}")
            return command
    
    def learn_from_command(self, command, category, success=True):
        """Learn from user commands"""
        try:
            if category in self.categories:
                self.command_learner.add_command(command, category)
                if success:
                    logger.info(f"Added new command to dataset: {command} ({category})")
                else:
                    logger.warning(f"Added failed command to dataset: {command} ({category})")
            else:
                logger.warning(f"Invalid category: {category}")
        except Exception as e:
            logger.error(f"Error learning from command: {e}")
    
    def _process_ai_queue(self):
        """Background thread for processing AI tasks"""
        while True:
            try:
                task = self.ai_queue.get()
                if task is None:
                    break
                    
                task_type, data = task
                result = None
                
                if task_type == "sentiment":
                    result = self.hf_helper.analyze_sentiment(data)
                elif task_type == "intent":
                    result = self.hf_helper.classify_intent(data["text"], data["intents"])
                elif task_type == "qa":
                    result = self.hf_helper.answer_question(data["context"], data["question"])
                elif task_type == "generate":
                    result = self.hf_helper.generate_response(data)
                
                if result:
                    self.results_cache[f"{task_type}_{data}"] = result
                
            except Exception as e:
                logger.error(f"Error in AI background processing: {e}")
            finally:
                self.ai_queue.task_done()
    
    def add_to_context(self, item: Dict[str, Any]):
        """Add item to context memory"""
        self.context_memory.append(item)
        if len(self.context_memory) > self.max_context_items:
            self.context_memory.pop(0)
    
    def get_context(self) -> str:
        """Get formatted context string"""
        return "\n".join([
            f"User: {item['user']}\nAssistant: {item['assistant']}"
            for item in self.context_memory
        ])
    
    def generate_response(self, command: str, context: Optional[str] = None) -> str:
        """Generate natural language response"""
        if context:
            prompt = f"Context: {context}\nUser: {command}\nAssistant:"
        else:
            prompt = f"User: {command}\nAssistant:"
            
        self.ai_queue.put(("generate", prompt))
        
        # Return immediate response while background processing continues
        return self.hf_helper.generate_response(prompt, max_length=50)
    
    def answer_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Answer questions using context"""
        if not context:
            context = self.get_context()
            
        self.ai_queue.put(("qa", {"context": context, "question": question}))
        
        # Get immediate answer
        result = self.hf_helper.answer_question(context, question)
        self.add_to_context({"user": question, "assistant": result["answer"]})
        return result
    
    def _process_sentiment_queue(self):
        """Process queued commands for sentiment in background"""
        try:
            while True:
                command = self.sentiment_queue.get()
                try:
                    # Simple rule-based sentiment analysis
                    positive_words = ["thanks", "good", "great", "awesome", "excellent", "please", "nice"]
                    negative_words = ["bad", "terrible", "awful", "stupid", "useless", "horrible"]
                    
                    # Convert to lowercase for comparison
                    command_lower = command.lower()
                    
                    # Count positive and negative words
                    positive_count = sum(1 for word in positive_words if word in command_lower)
                    negative_count = sum(1 for word in negative_words if word in command_lower)
                    
                    # Determine sentiment
                    if positive_count > negative_count:
                        sentiment = "positive"
                    elif negative_count > positive_count:
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"
                    
                    # Update context with sentiment
                    self.context["last_sentiment"] = sentiment
                    
                except Exception as e:
                    logger.error(f"Error in sentiment analysis: {e}")
                
                # Mark task as done
                self.sentiment_queue.task_done()
                
        except Exception as e:
            logger.error(f"Error in sentiment processing thread: {e}")
    
    def _update_command_history(self, command, category):
        """Update command history JSON file"""
        try:
            # Use the history file path from config
            history_path = config.get_nested("commands.training_files.history", "training_data/command_history.json")
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
                
                # Add command to history
                if "commands" not in history:
                    history["commands"] = []
                    
                history["commands"].append({
                    "text": command,
                    "category": category,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update categories
                if "categories" not in history:
                    history["categories"] = {}
                    
                if category not in history["categories"]:
                    history["categories"][category] = []
                    
                if command not in history["categories"][category]:
                    history["categories"][category].append(command)
                
                # Save updated history
                with open(history_path, 'w') as f:
                    json.dump(history, f, indent=4)
                    
        except Exception as e:
            logger.error(f"Error updating command history: {e}")
    
    def cleanup(self):
        """Clean up AI resources"""
        try:
            # Signal background thread to stop
            self.ai_queue.put(None)
            self.bg_thread.join(timeout=1)
            
            # Clear caches
            self.results_cache.clear()
            self.context_memory.clear()
            
            # Save command history context
            history_path = config.get_nested("commands.training_files.history", "training_data/command_history.json")
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
                
                # Add any remaining commands from context
                for cmd in self.context.get("command_history", []):
                    if cmd not in history["commands"]:
                        history["commands"].append(cmd)
                
                # Save updated history
                with open(history_path, 'w') as f:
                    json.dump(history, f, indent=4)
            
            logger.info("AI Orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in AI Orchestrator cleanup: {e}")
    
    def process_command(self, command: str, category: str) -> bool:
        """Process a command with a known category"""
        try:
            if not command or not category:
                return False
                
            logger.info(f"Processing command: '{command}' in category: {category}")
            
            # Process by category
            if category == "system_control":
                return self.system_controls.control_system(command)
                
            elif category == "media_control":
                if hasattr(self.media_controls, "handle_media") and callable(getattr(self.media_controls, "handle_media")):
                    return self.media_controls.process_media_command(command)
                elif hasattr(self.media_controls, "process_media_command") and callable(getattr(self.media_controls, "process_media_command")):
                    return self.media_controls.process_media_command(command)
                else:
                    logger.error("MediaControls class doesn't have a valid media command handling method")
                    return False
                
            elif category == "system_info":
                return self.get_system_info(command)
                
            elif category == "screenshot":
                return self.system_controls.take_screenshot()
                
            elif category == "video_control":
                # Check if this might be a YouTube search instead of actual video control
                if any(word in command.lower() for word in ["youtube", "search", "find", "watch"]):
                    if "play" in command.lower():
                        # Likely a "play X on YouTube" command
                        return self.web_search.handle_youtube_command(command)
                    else:
                        # Other YouTube-related command
                        return self.web_search.handle_youtube_command(command)
                    
                # If it's an actual control command, use control_playback
                return self.web_search.youtube_handler.control_playback(command)
                
            elif category == "youtube_search" or "youtube" in command.lower():
                # Handle YouTube specific commands
                if "play" in command.lower():
                    search_query = command.lower().replace("play", "").replace("youtube", "").replace("on", "").strip()
                    return self.web_search.handle_youtube_command(command)
                else:
                    search_query = command.lower().replace("search", "").replace("youtube", "").replace("for", "").strip()
                    return self.web_search.handle_youtube_command(command)
                
            elif category == "youtube_play":
                search_query = command.lower().replace("play", "").replace("youtube", "").replace("on", "").strip()
                return self.web_search.handle_youtube_command(command)
                
            elif category == "web_search":
                # If command contains YouTube but was misclassified
                if "youtube" in command.lower():
                    if "play" in command.lower():
                        search_query = command.lower().replace("play", "").replace("youtube", "").replace("on", "").strip()
                        return self.web_search.handle_youtube_command(command)
                    else:
                        search_query = command.lower().replace("search", "").replace("youtube", "").replace("for", "").strip()
                        return self.web_search.handle_youtube_command(command)
                else:
                    return self.web_search.search_web(command)
                
            else:
                return self.process_uncertain_command(command)
                
        except Exception as e:
            logger.error(f"Error in process_command: {e}")
            return False
    
    def process_uncertain_command(self, command: str) -> bool:
        """Process a command with uncertain category"""
        try:
            # For uncertain commands, default to web search
            logger.info(f"Processing uncertain command: '{command}'")
            return self.web_search.search_web(command)
            
        except Exception as e:
            logger.error(f"Error in process_uncertain_command: {e}")
            return False
    
    def get_time(self) -> bool:
        """Get the current time"""
        try:
            current_time = datetime.now().strftime("%I:%M %p")
            print(f"Current time: {current_time}")
            speak(f"The current time is {current_time}")
            return True
        except Exception as e:
            logger.error(f"Error getting time: {e}")
            return False
    
    def get_date(self) -> bool:
        """Get the current date"""
        try:
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            print(f"Current date: {current_date}")
            speak(f"Today is {current_date}")
            return True
        except Exception as e:
            logger.error(f"Error getting date: {e}")
            return False
    
    def get_system_info(self, command: str = None) -> bool:
        """Get system information based on command"""
        try:
            # CPU usage
            if command and any(word in command.lower() for word in ["cpu", "processor"]):
                cpu_percent = psutil.cpu_percent(interval=1)
                print(f"CPU Usage: {cpu_percent}%")
                speak(f"CPU usage is {cpu_percent} percent")
                return True
                
            # Memory usage
            elif command and any(word in command.lower() for word in ["memory", "ram"]):
                memory = psutil.virtual_memory()
                used_memory = round(memory.used / (1024 ** 3), 2)
                total_memory = round(memory.total / (1024 ** 3), 2)
                print(f"Memory Usage: {used_memory} GB / {total_memory} GB ({memory.percent}%)")
                speak(f"Memory usage is {memory.percent} percent, {used_memory} gigabytes used out of {total_memory} gigabytes")
                return True
                
            # Disk usage
            elif command and any(word in command.lower() for word in ["disk", "storage", "drive"]):
                try:
                    # Get disk stats
                    disk = psutil.disk_usage('/')
                    
                    # Calculate values
                    used_gb = disk.used / (1024 * 1024 * 1024)
                    total_gb = disk.total / (1024 * 1024 * 1024)
                    percent = disk.percent
                    
                    # Round numbers
                    used_gb_rounded = round(used_gb, 2)
                    total_gb_rounded = round(total_gb, 2)
                    
                    # Print first, then speak
                    disk_message = "Disk Usage: " + str(used_gb_rounded) + " GB / " + str(total_gb_rounded) + " GB (" + str(percent) + "%)"
                    print(disk_message)
                    
                    # Create speech message
                    speech_message = "Disk usage is " + str(percent) + " percent"
                    speak(speech_message)
                    
                    return True
                except Exception as disk_e:
                    logger.error(f"Error checking disk space: {disk_e}")
                    print("Error checking disk space")
                    speak("I was unable to check disk space")
                    return False
                
            # General system info
            else:
                system_info = f"OS: {platform.system()} {platform.version()}"
                print(system_info)
                speak(f"You are running {platform.system()} version {platform.version()}")
                return True
                
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return False
    
    def get_battery_status(self) -> bool:
        """Get battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                power_plugged = battery.power_plugged
                status = "plugged in" if power_plugged else "on battery"
                print(f"Battery: {percent}% ({status})")
                speak(f"Battery is at {percent} percent and {status}")
                return True
            else:
                print("No battery detected")
                speak("No battery detected")
                return False
        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            return False
    
    def get_wifi_status(self) -> bool:
        """Get WiFi status"""
        try:
            # Check network connectivity (simplified)
            connected = False
            try:
                if platform.system() == "Windows":
                    output = subprocess.check_output("netsh wlan show interfaces", shell=True)
                    output_str = output.decode('utf-8')
                    
                    if "State" in output_str and "connected" in output_str:
                        connected = True
                        ssid = None
                        for line in output_str.split('\n'):
                            if "SSID" in line and "BSSID" not in line:
                                ssid = line.split(":")[1].strip()
                                break
                        
                        print(f"WiFi: Connected to {ssid}")
                        speak(f"WiFi is connected to {ssid}")
                        return True
                else:
                    # For other platforms
                    connected = True
                    print("WiFi: Connected")
                    speak("WiFi is connected")
                    return True
            except:
                pass
                
            if not connected:
                print("WiFi: Not connected")
                speak("WiFi is not connected")
                return False
                
        except Exception as e:
            logger.error(f"Error getting WiFi status: {e}")
            return False
    
    def get_news(self) -> bool:
        """Get news headlines"""
        try:
            print("Fetching news headlines...")
            speak("Here are the latest news headlines")
            return self.web_search.search_web("latest news")
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return False 