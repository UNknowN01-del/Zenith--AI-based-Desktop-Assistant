    def predict_category(self, command, min_confidence=0.3):
        """
        Predict the category of a command with confidence score.
        
        Args:
            command (str): The command to categorize
            min_confidence (float): The minimum confidence threshold
            
        Returns:
            tuple: (predicted_category, confidence_score)
        """
        try:
            if not command or command.strip() == "":
                return "unknown", 0.0
            
            # Clean and prepare the command
            cleaned_command = self._clean_text(command.lower())
            
            # Direct pattern matches for high confidence predictions
            # System information commands
            if any(keyword in cleaned_command for keyword in ["cpu", "processor", "memory", "ram", 
                                                              "disk space", "storage", "system info"]):
                return "system_info", 1.0
                
            # Weather information commands - direct high confidence match
            if any(keyword in cleaned_command for keyword in ["weather", "temperature outside", "forecast"]):
                return "system_info", 1.0
                
            # Brightness and volume are system controls, not media controls
            if any(keyword in cleaned_command for keyword in ["brightness", "screen bright", "dim screen", 
                                                             "volume", "sound level", "mute", "unmute"]):
                return "system_control", 0.95
            
            # ... existing code ...
        except Exception as e:
            print(f"Error predicting category: {e}")
            return "unknown", 0.0 