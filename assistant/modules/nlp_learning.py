#!/usr/bin/env python
import os
import json
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import joblib
import spacy
import logging
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from typing import Dict, List, Tuple, Any, Optional
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandLearner:
    def __init__(self):
        """Initialize the command learning system"""
        self.model = None
        self.vectorizer = None
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
        
        # Load or create training data
        self.training_data = self._load_training_data()
        
        # Train model if we have data
        if self.training_data:
            self._train_model()
        
        logger.info("Command learner initialized")
    
    def _load_training_data(self):
        """Load training data from JSON file"""
        try:
            # Initialize with some default commands
            default_commands = {
                "screenshot": [
                    "take a screenshot",
                    "capture screen",
                    "screenshot please",
                    "take screenshot",
                    "grab screenshot",
                    "save screen"
                ],
                "youtube_search": [
                    "search youtube for",
                    "find videos of",
                    "search for videos",
                    "look up on youtube",
                    "youtube search"
                ],
                "youtube_play": [
                    "play on youtube",
                    "play video",
                    "start playing",
                    "youtube play",
                    "watch video"
                ],
                "system_control": [
                    "open chrome",
                    "launch notepad",
                    "start calculator",
                    "minimize window",
                    "maximize window"
                ],
                "media_control": [
                    "pause video",
                    "play music",
                    "stop playback",
                    "next track",
                    "volume up"
                ],
                "system_info": [
                    "check cpu usage",
                    "show memory",
                    "battery status",
                    "system information",
                    "show temperature"
                ],
                "web_search": [
                    "search for",
                    "look up",
                    "find information about",
                    "google",
                    "search web for"
                ]
            }
            
            # Try to load existing data
            if os.path.exists("training_data/command_dataset.json"):
                with open("training_data/command_dataset.json", "r") as f:
                    json_data = json.load(f)
                
                # Check if the file is in the new format (with 'commands' array)
                if "commands" in json_data:
                    # Convert new format to old format for compatibility
                    data = {}
                    for cmd in json_data.get("commands", []):
                        if isinstance(cmd, dict) and "category" in cmd and "text" in cmd:
                            category = cmd["category"]
                            text = cmd["text"]
                            if category not in data:
                                data[category] = []
                            if text not in data[category]:
                                data[category].append(text)
                else:
                    # Old format - direct dictionary mapping
                    data = json_data
                
                # Merge with default commands
                for category in default_commands:
                    if category not in data:
                        data[category] = default_commands[category]
                    else:
                        # Add any missing default commands
                        data[category].extend([cmd for cmd in default_commands[category] 
                                            if cmd not in data[category]])
            else:
                data = default_commands
                
            # Save merged data in old format for compatibility
            os.makedirs("training_data", exist_ok=True)
            with open("training_data/command_dataset_old.json", "w") as f:
                json.dump(data, f, indent=4)
                
            return data
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return None
    
    def _train_model(self):
        """Train the command classification model"""
        try:
            if not self.training_data:
                logger.warning("No training data available. Cannot train model.")
                return
                
            # Prepare training data
            X = []  # Commands
            y = []  # Categories
            
            for category, commands in self.training_data.items():
                for command in commands:
                    if isinstance(command, str):  # Ensure command is a string
                        X.append(command.lower())
                        y.append(category)
            
            if not X or not y:
                logger.warning("Empty training data. Cannot train model.")
                return
                
            # Create and train vectorizer
            self.vectorizer = TfidfVectorizer(
                analyzer='word',
                ngram_range=(1, 2),
                max_features=1000
            )
            X_vectorized = self.vectorizer.fit_transform(X)
            
            # Train model
            self.model = MultinomialNB()
            self.model.fit(X_vectorized, y)
            
            # Evaluate model
            y_pred = self.model.predict(X_vectorized)
            report = classification_report(y, y_pred)
            logger.info("Model evaluation:\n" + report)
            
            # Save model
            self._save_model()
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def predict_category(self, command):
        """Predict category for a command"""
        try:
            if not command or not isinstance(command, str):
                return "web_search", 0.3
            
            # Clean command
            command = command.lower().strip()
            
            # Direct category assignments with high confidence
            
            # System power control commands
            if any(phrase in command for phrase in ["lock computer", "lock system", "lock pc", "shutdown", "restart computer", "restart system", "restart pc", "power off", "turn off computer"]):
                return "system_control", 0.95
            
            # Time and date commands
            if any(phrase in command for phrase in ["what time", "current time", "what's the time", "tell me the time"]):
                return "system_info", 0.95
            
            if any(phrase in command for phrase in ["what date", "current date", "what's the date", "today's date", "what day"]):
                return "system_info", 0.95
            
            # System info commands with direct matches
            if any(phrase in command for phrase in ["battery", "cpu", "memory", "ram", "disk space", "wifi", "system information", "system info"]):
                return "system_info", 0.95
            
            # Window control commands
            if any(phrase in command for phrase in ["minimize window", "minimise window", "maximize window", "maximise window", "restore window", "minimize", "minimise", "maximize", "maximise"]):
                return "system_control", 0.95
                
            # Volume and brightness control
            if any(phrase in command for phrase in ["volume up", "volume down", "increase volume", "decrease volume", "set volume", "mute", "unmute"]):
                return "system_control", 0.95
                
            if any(phrase in command for phrase in ["brightness up", "brightness down", "increase brightness", "decrease brightness", "set brightness"]):
                return "system_control", 0.95
            
            # Check for direct matches from training data
            for category, commands in self.training_data.items():
                if any(isinstance(cmd, str) and cmd.lower() == command for cmd in commands):
                    return category, 0.95  # Exact match has high confidence
                elif any(isinstance(cmd, str) and cmd.lower() in command for cmd in commands):
                    return category, 0.9   # Partial match has slightly lower confidence
            
            # YouTube specific checks with improved patterns
            youtube_pattern = re.compile(r'(youtube|video|play|watch)', re.IGNORECASE)
            search_pattern = re.compile(r'(search|find|look)', re.IGNORECASE)
            
            if youtube_pattern.search(command):
                if search_pattern.search(command):
                    return "youtube_search", 0.9
                elif "play" in command:
                    return "youtube_play", 0.9
                else:
                    return "video_control", 0.8
            
            # Screenshot specific checks
            if any(word in command for word in ["screenshot", "capture screen", "grab screen"]):
                return "screenshot", 0.9
            
            # Use model for other cases
            if self.model and self.vectorizer:
                X = self.vectorizer.transform([command])
                category = self.model.predict(X)[0]
                confidence = max(self.model.predict_proba(X)[0])
                
                # If confidence is very low, default to web search
                if confidence < 0.3:
                    return "web_search", 0.5
                    
                return category, confidence
            
            return "web_search", 0.3
            
        except Exception as e:
            logger.error(f"Error predicting category: {e}")
            return "web_search", 0.3
    
    def add_command(self, command, category):
        """Add a new command to the training data"""
        try:
            if category not in self.categories:
                logger.warning(f"Invalid category: {category}")
                return False
            
            # Add to training data
            if category not in self.training_data:
                self.training_data[category] = []
            
            command = command.lower().strip()
            if command not in self.training_data[category]:
                self.training_data[category].append(command)
                logger.info(f"Added new command directly to dataset: {command} ({category})")
                
                # Save updated data
                with open("training_data/command_dataset.json", "w") as f:
                    json.dump(self.training_data, f, indent=4)
                
                # Retrain model
                self._train_model()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding command: {e}")
            return False
    
    def _save_model(self):
        """Save the trained model"""
        try:
            os.makedirs("models", exist_ok=True)
            with open("models/command_classifier.pkl", "wb") as f:
                pickle.dump({
                    'model': self.model,
                    'vectorizer': self.vectorizer
                }, f)
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load a trained model"""
        try:
            if os.path.exists("models/command_classifier.pkl"):
                with open("models/command_classifier.pkl", "rb") as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.vectorizer = data['vectorizer']
                logger.info("Model is already trained and ready")
                return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
        return False

    def ensure_model_is_trained(self):
        """Ensure the model is fitted with at least basic data"""
        try:
            # Create basic dataset if we don't have one
            if not self.training_data:
                logger.info("No existing dataset found. Creating basic training dataset.")
                self._train_model()
                logger.info("Created and saved basic command dataset")
            
            # Check if model is already fitted
            try:
                # Try a simple prediction to see if model is fitted
                self.predict_category("test command")
                logger.info("Model is already trained and ready")
            except Exception as e:
                logger.warning(f"Model needs initial training: {e}")
                # Train the model with the dataset
                self._train_model()
                logger.info("Initial model training completed")
                
        except Exception as e:
            logger.error(f"Error ensuring model is trained: {e}")

    def preprocess_text(self, text):
        """Enhanced text preprocessing"""
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token.isalnum() and token not in self.stop_words]
        
        # Join tokens back into text
        return ' '.join(tokens)

    def load_command_dataset(self):
        """Load the pre-trained command dataset"""
        try:
            if os.path.exists("training_data/command_dataset.json"):
                with open("training_data/command_dataset.json", 'r') as f:
                    return json.load(f)
            logger.warning(f"Command dataset not found at training_data/command_dataset.json")
            return {'commands': [], 'categories': {}}
        except Exception as e:
            logger.error(f"Error loading command dataset: {e}")
            return {'commands': [], 'categories': {}}

    def load_new_commands(self):
        """Load new commands that need verification"""
        try:
            if os.path.exists("training_data/new_commands.json"):
                with open("training_data/new_commands.json", 'r') as f:
                    return json.load(f)
            return {'commands': [], 'categories': {}}
        except Exception as e:
            logger.error(f"Error loading new commands: {e}")
            return {'commands': [], 'categories': {}}

    def save_new_commands(self, new_commands):
        """Save new commands for manual review with proper categories organization"""
        try:
            # Ensure the categories dictionary exists and is properly structured
            if 'categories' not in new_commands:
                new_commands['categories'] = {}
                
            # Rebuild categories dictionary from commands to ensure consistency
            categories = {}
            for cmd in new_commands['commands']:
                if cmd['category'] not in categories:
                    categories[cmd['category']] = []
                # Only add text if not already in the category array
                if cmd['text'] not in categories[cmd['category']]:
                    categories[cmd['category']].append(cmd['text'])
            
            # Update the categories in the new_commands dictionary
            new_commands['categories'] = categories
            
            # Save to new commands file
            with open("training_data/new_commands.json", 'w') as f:
                json.dump(new_commands, f, indent=4)
                
            logger.info("New commands saved for review")
        except Exception as e:
            logger.error(f"Error saving new commands: {e}")

    def load_or_create_model(self):
        """Load existing model or create a new one with improved architecture"""
        try:
            if self._load_model():
                return self.model
            
            logger.info("Creating new model")
            return Pipeline([
                ('tfidf', TfidfVectorizer(
                    preprocessor=self.preprocess_text,
                    ngram_range=(1, 3),  # Include up to trigrams for better phrase matching
                    max_features=10000,  # Increase features for better discrimination
                    min_df=2,  # Minimum document frequency
                    use_idf=True,
                    sublinear_tf=True  # Apply sublinear tf scaling
                )),
                ('clf', RandomForestClassifier(
                    n_estimators=200,  # More trees for better accuracy
                    max_depth=15,  # Deeper trees for more complex patterns
                    min_samples_split=4,  # Require more samples to split
                    class_weight='balanced',  # Handle class imbalance
                    random_state=42
                ))
            ])
        except Exception as e:
            logger.error(f"Error loading/creating model: {e}")
            return None

    def save_model(self):
        """Save the trained model"""
        try:
            self._save_model()
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def get_similar_commands(self, command, category=None):
        """Get similar commands from history with improved similarity scoring"""
        try:
            if not self.training_data:
                return []
                
            if category and category in self.training_data:
                commands = self.training_data[category]
            else:
                commands = [cmd for cmd in self.training_data.values()]
                commands = [cmd for sublist in commands for cmd in sublist]
            
            # Use spaCy for similarity comparison
            doc1 = self.nlp(command)
            similarities = []
            
            for cmd in commands:
                doc2 = self.nlp(cmd)
                similarity = doc1.similarity(doc2)
                similarities.append((cmd, similarity))
                
            # Return top 3 most similar commands
            return sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
        except Exception as e:
            logger.error(f"Error finding similar commands: {e}")
            return []

    def get_command_suggestions(self, partial_command):
        """Get command suggestions based on partial input with fuzzy matching"""
        try:
            if not self.training_data:
                return []
                
            all_commands = [cmd for cmds in self.training_data.values() for cmd in cmds]
            suggestions = []
            
            # Convert to lowercase for case-insensitive matching
            partial_command = partial_command.lower()
            
            for cmd in all_commands:
                cmd_lower = cmd.lower()
                if cmd_lower.startswith(partial_command):
                    suggestions.append(cmd)
                elif partial_command in cmd_lower:
                    suggestions.append(cmd)
                    
            return suggestions[:5]  # Return top 5 suggestions
        except Exception as e:
            logger.error(f"Error getting command suggestions: {e}")
            return []

    def update_model(self):
        """Manual method to update the model with verified commands"""
        try:
            # Load new verified commands
            new_commands = self.load_new_commands()
            
            if not new_commands['commands']:
                logger.info("No new commands to verify")
                return False
            
            # Load existing dataset to avoid duplicates
            existing_texts = [cmd.lower() for cmd in self.training_data.values()]
            
            # Add verified commands to the main dataset, avoiding duplicates
            added_count = 0
            for cmd in new_commands['commands']:
                if cmd['text'].lower() not in existing_texts:
                    self.training_data[cmd['category']].append(cmd['text'])
                    added_count += 1
                    existing_texts.append(cmd['text'].lower())
            
            # Save updated dataset
            with open("training_data/command_dataset.json", 'w') as f:
                json.dump(self.training_data, f, indent=4)
            
            # Train model with updated data
            self._train_model()
            
            # Clear new commands file
            self.save_new_commands({'commands': [], 'categories': {}})
            
            logger.info(f"Added {added_count} new unique commands to the dataset")
            
            logger.info("Model updated with verified commands")
            return True
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            return False

    def get_category_confidence(self, command):
        """Enhanced category confidence calculation with video command handling"""
        try:
            if not command:
                logger.warning("Empty command received")
                return {'category': 'web_search', 'confidence': 0.3, 'method': 'default_empty'}
            
            # Convert to lowercase for consistent matching
            command_lower = command.lower()
            
            # First check for direct video control commands
            direct_video_commands = {
                'play': 0.95,
                'pause': 0.95,
                'stop': 0.95,
                'resume': 0.95,
                'next video': 0.95,
                'previous video': 0.95
            }
            
            # Check if it's a direct video command
            if command_lower in direct_video_commands:
                return {
                    'category': 'video_control',
                    'confidence': direct_video_commands[command_lower],
                    'method': 'direct_match',
                    'action': command_lower
                }
            
            # Check for video control patterns
            for pattern in self.command_patterns['video_control']:
                if re.match(pattern, command_lower):
                    return {
                        'category': 'video_control',
                        'confidence': 0.9,
                        'method': 'pattern_match_video',
                        'action': self._extract_video_action(command_lower)
                    }
            
            # Rest of the category prediction logic...
            # ... existing code ...

        except Exception as e:
            logger.error(f"Error in category prediction: {e}")
            return {
                'category': 'web_search',
                'confidence': 0.5,
                'method': 'error_fallback'
            }

    def _extract_video_action(self, command: str) -> Dict[str, Any]:
        """Extract specific video action and parameters from command"""
        action = {
            'type': None,
            'parameters': {}
        }
        
        # Check for basic playback controls
        if any(cmd in command for cmd in ['play', 'pause', 'stop', 'resume']):
            action['type'] = 'playback_control'
            action['parameters']['command'] = next(cmd for cmd in ['play', 'pause', 'stop', 'resume'] if cmd in command)
        
        # Check for navigation controls
        elif any(cmd in command for cmd in ['next', 'previous', 'skip']):
            action['type'] = 'navigation'
            action['parameters']['direction'] = 'next' if any(cmd in command for cmd in ['next', 'skip']) else 'previous'
        
        # Check for time-based controls
        elif re.search(r'(?P<time>\d+)\s*(seconds?|minutes?|mins?|secs?)', command):
            action['type'] = 'seek'
            match = re.search(r'(?P<time>\d+)\s*(?P<unit>seconds?|minutes?|mins?|secs?)', command)
            if match:
                time = int(match.group('time'))
                unit = match.group('unit')
                # Convert to seconds if necessary
                if unit.startswith(('minute', 'min')):
                    time *= 60
                action['parameters']['time'] = time
        
        # Check for YouTube search
        elif 'youtube' in command:
            action['type'] = 'youtube_search'
            # Extract search query
            query_match = re.search(r'(?:play|search|find|watch)\s+(?P<query>.+?)(?:\s+(?:on|in)\s+youtube)?$', command)
            if query_match:
                action['parameters']['query'] = query_match.group('query')
        
        return action

    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parse a command using sophisticated pattern matching and context awareness.
        Returns a dictionary with parsed command information.
        """
        # Initialize result dictionary
        result = {
            'original_command': command,
            'normalized_command': None,
            'category': None,
            'parameters': {},
            'compound_commands': [],
            'confidence': 0.0,
            'requires_context': False
        }
        
        # Check for compound commands first
        for pattern in self.command_patterns['compound']:
            match = re.match(pattern, command)
            if match:
                result['compound_commands'] = [
                    match.group('cmd1').strip(),
                    match.group('cmd2').strip()
                ]
                return result
        
        # Check if this is a contextual follow-up command
        for pattern in self.command_patterns['contextual']:
            if re.match(pattern, command):
                result['requires_context'] = True
                result['category'] = self.command_context['last_category']
                result['parameters'] = self.command_context['last_parameters'].copy()
                return result
        
        # Try exact pattern matching first
        for category, patterns in self.command_patterns.items():
            if category in ['compound', 'contextual', 'parameters']:
                continue
                
            for pattern in patterns:
                match = re.match(pattern, command)
                if match:
                    result['category'] = category
                    result['parameters'] = match.groupdict()
                    result['confidence'] = 0.9
                    return result
        
        # If no exact match, try fuzzy matching
        best_match = None
        highest_score = 0
        
        for category, patterns in self.command_patterns.items():
            if category in ['compound', 'contextual', 'parameters']:
                continue
                
            for pattern in patterns:
                # Convert regex pattern to a template string for comparison
                template = re.sub(r'\(\?P<[^>]+>\[^\)]+\)', '', pattern)
                template = re.sub(r'[\(\)\?\*\+]', '', template)
                
                score = fuzz.ratio(command.lower(), template.lower())
                if score > highest_score and score >= self.fuzzy_threshold:
                    highest_score = score
                    best_match = (category, pattern)
        
        if best_match:
            category, pattern = best_match
            result['category'] = category
            result['confidence'] = highest_score / 100.0
            
            # Try to extract parameters even with fuzzy match
            match = re.match(pattern, command)
            if match:
                result['parameters'] = match.groupdict()
        
        # Update command context
        self.command_context['last_command'] = command
        self.command_context['last_category'] = result['category']
        self.command_context['last_parameters'] = result['parameters']
        
        return result

    def extract_parameters(self, command: str) -> Dict[str, Any]:
        """
        Extract parameters from a command string using sophisticated pattern matching.
        """
        parameters = {}
        
        # Try all parameter patterns
        for pattern in self.command_patterns['parameters']:
            matches = re.finditer(pattern, command)
            for match in matches:
                parameters.update(match.groupdict())
        
        # Convert numeric values
        for key, value in parameters.items():
            if value and value.isdigit():
                parameters[key] = int(value)
        
        return parameters

    def normalize_command(self, command: str) -> str:
        """
        Normalize command text to handle variations and misspellings.
        """
        # Convert to lowercase
        normalized = command.lower()
        
        # Handle common misspellings and variations
        variations = {
            'shutdown': ['shut down', 'shutdwn', 'shut-down'],
            'logout': ['log out', 'log-out', 'signout', 'sign out'],
            'restart': ['re start', 're-start', 'reboot'],
            'volume': ['vol', 'sound', 'audio'],
            'brightness': ['bright', 'display brightness', 'screen brightness'],
        }
        
        # Replace variations with standard forms
        for standard, variants in variations.items():
            for variant in variants:
                normalized = re.sub(r'\b' + re.escape(variant) + r'\b', standard, normalized)
        
        return normalized 

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a command with enhanced pattern recognition and context awareness.
        """
        # Normalize the command first
        normalized_command = self.normalize_command(command)
        
        # Parse the command
        result = self.parse_command(normalized_command)
        
        # Handle compound commands
        if result['compound_commands']:
            compound_results = []
            for cmd in result['compound_commands']:
                sub_result = self.parse_command(cmd)
                compound_results.append(sub_result)
            result['compound_results'] = compound_results
        
        # Handle contextual commands
        if result['requires_context']:
            if not self.command_context['last_command']:
                result['error'] = "No previous command context available"
                return result
                
            # Update parameters based on context
            if 'amount' in result['parameters']:
                amount = result['parameters']['amount']
                if 'more' in normalized_command:
                    # Increase the previous value
                    if 'level' in self.command_context['last_parameters']:
                        result['parameters']['level'] = min(
                            100,
                            self.command_context['last_parameters']['level'] + (amount or 10)
                        )
                elif 'less' in normalized_command:
                    # Decrease the previous value
                    if 'level' in self.command_context['last_parameters']:
                        result['parameters']['level'] = max(
                            0,
                            self.command_context['last_parameters']['level'] - (amount or 10)
                        )
        
        # Extract any additional parameters
        additional_params = self.extract_parameters(normalized_command)
        result['parameters'].update(additional_params)
        
        # Enhance confidence based on parameter extraction
        if additional_params and result['confidence'] < 0.9:
            result['confidence'] = min(0.9, result['confidence'] + 0.1)
        
        return result

    def get_command_variations(self, command: str) -> List[str]:
        """
        Generate variations of a command to handle different phrasings.
        """
        variations = [command]
        doc = self.nlp(command)
        
        # Generate variations using spaCy's linguistic features
        for token in doc:
            # Handle synonyms
            if token.pos_ in ['VERB', 'ADJ', 'ADV']:
                for synset in nltk.wordnet.wordnet.synsets(token.text):
                    for lemma in synset.lemmas():
                        if lemma.name() != token.text:
                            variation = command.replace(token.text, lemma.name())
                            variations.append(variation)
            
            # Handle word order variations
            if token.dep_ in ['compound', 'amod']:
                # Create variation with and without the modifier
                variation = command.replace(token.text + ' ', '')
                variations.append(variation)
        
        return list(set(variations))

    def suggest_corrections(self, command: str) -> List[Tuple[str, float]]:
        """
        Suggest corrections for potentially misspelled commands.
        """
        corrections = []
        words = command.split()
        
        for word in words:
            # Check against known command words
            known_words = set()
            for patterns in self.command_patterns.values():
                for pattern in patterns:
                    # Extract words from pattern
                    pattern_words = re.findall(r'\w+', pattern)
                    known_words.update(pattern_words)
            
            # Find similar words using fuzzy matching
            matches = process.extract(
                word,
                known_words,
                limit=3,
                scorer=fuzz.ratio
            )
            
            for match, score in matches:
                if score >= self.fuzzy_threshold and match != word:
                    corrected_command = command.replace(word, match)
                    corrections.append((corrected_command, score/100.0))
        
        return sorted(corrections, key=lambda x: x[1], reverse=True) 