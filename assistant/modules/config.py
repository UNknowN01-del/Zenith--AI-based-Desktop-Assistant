# Hugging Face API configuration
HUGGINGFACE_API_KEY = ""  # You can set your API key here if you have one

# Speech recognition settings
SPEECH_RECOGNITION = {
    "timeout": 5,
    "phrase_time_limit": 5,
    "language": "en-US"
}

# System settings
SYSTEM = {
    "screenshot_dir": "screenshots",
    "models_dir": "models",
    "training_data_dir": "training_data"
}

# Command confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
    "low": 0.4
}

# Media control settings
MEDIA = {
    "volume_step": 10,
    "brightness_step": 10
}

# Web search settings
WEB = {
    "search_engine": "google",
    "results_limit": 5
} 