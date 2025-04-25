#!/usr/bin/env python
"""
Configuration Handler for AI Desktop Assistant

This module handles loading and managing configuration settings
from the config.json file. It provides default settings if the 
configuration file is not found.
"""

import os
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ConfigHandler:
    """Manages configuration settings for the AI Desktop Assistant"""
    
    def __init__(self, config_path="config.json"):
        """Initialize the configuration handler
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from file or use defaults"""
        default_config = {
            "assistant": {
                "name": "AI Desktop Assistant",
                "version": "1.0.0",
                "user": "user",
                "voice": {
                    "rate": 180,
                    "volume": 1.0,
                    "prefer_indian_voice": True
                },
                "logging": {
                    "level": "INFO",
                    "file": "assistant.log",
                    "max_size_mb": 5,
                    "backup_count": 3
                }
            },
            "commands": {
                "confidence_threshold": {
                    "low": 0.4,
                    "medium": 0.7,
                    "high": 0.9
                },
                "categories": [
                    "system_control",
                    "media_control",
                    "system_info",
                    "web_search",
                    "video_control",
                    "screenshot",
                    "info_request"
                ],
                "training_files": {
                    "dataset": "training_data/command_dataset.json",
                    "new_commands": "training_data/new_commands.json",
                    "history": "training_data/command_history.json"
                }
            },
            "paths": {
                "screenshots": "screenshots",
                "media": {
                    "audio": "media/audio",
                    "video": "media/video"
                },
                "models": "models"
            },
            "features": {
                "brightness_control": {
                    "enabled": True,
                    "step_size": 10
                },
                "volume_control": {
                    "enabled": True,
                    "step_size": 10
                },
                "youtube": {
                    "enabled": True,
                    "default_browser": ""
                },
                "web_search": {
                    "default_engine": "google",
                    "speak_results": False
                },
                "system_control": {
                    "confirm_shutdown": True,
                    "confirm_restart": True
                }
            },
            "api_keys": {
                "weather": "",
                "news": "",
                "google_speech": ""
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                
                # Merge with default config to ensure all settings are present
                # This approach ensures backward compatibility if new settings are added
                self._merge_configs(default_config, loaded_config)
                return default_config
            else:
                logger.warning(f"Configuration file {self.config_path} not found. Using defaults")
                # Create default config file
                self.save_config(default_config)
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
    
    def _merge_configs(self, default_config, loaded_config):
        """Recursively merge loaded config into default config"""
        for key, value in loaded_config.items():
            if key in default_config:
                if isinstance(value, dict) and isinstance(default_config[key], dict):
                    # Recursively merge nested dictionaries
                    self._merge_configs(default_config[key], value)
                else:
                    # Replace default value with loaded value
                    default_config[key] = value
            else:
                # Add new keys from loaded config
                default_config[key] = value
    
    def get(self, section, key=None, default=None):
        """Get a configuration value
        
        Args:
            section (str): Section of configuration
            key (str, optional): Key within section. If None, returns entire section
            default (any, optional): Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            if section in self.config:
                if key is None:
                    return self.config[section]
                elif key in self.config[section]:
                    return self.config[section][key]
            return default
        except Exception as e:
            logger.error(f"Error retrieving config {section}.{key}: {e}")
            return default
    
    def get_nested(self, path, default=None):
        """Get a nested configuration value using dot notation
        
        Args:
            path (str): Path using dot notation (e.g., 'assistant.voice.rate')
            default (any, optional): Default value if path not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = path.split('.')
            value = self.config
            for key in keys:
                if key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception as e:
            logger.error(f"Error retrieving nested config {path}: {e}")
            return default
    
    def save_config(self, config=None):
        """Save configuration to file
        
        Args:
            config (dict, optional): Configuration to save. If None, saves current config
        """
        try:
            if config is None:
                config = self.config
                
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def update(self, section, key, value):
        """Update a configuration value and save to file
        
        Args:
            section (str): Section of configuration
            key (str): Key within section
            value (any): New value
        """
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section][key] = value
            self.save_config()
            logger.info(f"Configuration updated: {section}.{key}")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def update_nested(self, path, value):
        """Update a nested configuration value using dot notation
        
        Args:
            path (str): Path using dot notation (e.g., 'assistant.voice.rate')
            value (any): New value
        """
        try:
            keys = path.split('.')
            config = self.config
            
            # Navigate to the second-last key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
                
            # Update the last key
            config[keys[-1]] = value
            self.save_config()
            logger.info(f"Configuration updated: {path}")
        except Exception as e:
            logger.error(f"Error updating nested configuration: {e}")

# Create a singleton instance
config = ConfigHandler() 