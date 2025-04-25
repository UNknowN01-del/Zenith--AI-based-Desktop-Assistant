# AI Desktop Assistant

An intelligent desktop assistant that uses speech recognition, natural language processing, and AI to help with various tasks. This assistant features minimal verbosity and high confidence command prediction for a smooth user experience.

## Features

- **Voice Commands & Speech Recognition**: Accurate speech recognition with minimal feedback
- **Confidence Scoring**: Shows confidence levels for predicted commands
- **Compound Commands**: Process multiple commands at once using conjunctions like "and", "then"
- **YouTube Integration**: Search and play specific videos (first, second, etc.)
- **System Controls**: Open applications, manage windows, shutdown/restart/lock
- **System Information**: CPU usage, memory, disk space, battery status, Wi-Fi info
- **Media Controls**: Volume adjustment, playback controls (play/pause/next/previous)
- **Brightness Control**: Adjust screen brightness directly through system APIs
- **Web Integration**: Web searches, news headlines, weather information
- **Screenshots**: Take and save screenshots with timestamp naming
- **Windows Management**: Minimize, maximize, restore, and close windows
- **Intelligent Command Classification**: Categorizes commands with confidence scores

## Project Structure

```
AI_Desktop_Assistant/
├── assistant/           # Core assistant modules
│   └── modules/         # Individual feature modules
│       ├── advanced_features.py  # Advanced system controls and media features
│       ├── ai_orchestrator.py    # AI command processing and confidence scoring
│       ├── nlp_learning.py       # NLP and ML for command learning
│       ├── speech_utils.py       # Speech recognition and synthesis
│       ├── system_controls.py    # System operations and application controls
│       └── web_search.py         # Web searching and YouTube integration
├── media/               # Media folders
│   ├── audio/          # Audio files for playback
│   └── video/          # Video files for playback
├── screenshots/         # Saved screenshots
├── requirements.txt     # Dependencies
└── run.py              # Main execution file
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Zenith--AI-based-Desktop-Assistant.git
cd AI_Desktop_Assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the assistant:
```bash
python run.py
```

## Available Commands

### System Commands
- **Applications**: "open chrome", "open notepad", "launch calculator"
- **Window Management**: "minimize window", "maximize window", "restore window", "close window"
- **System Control**: "shutdown computer", "restart computer", "lock computer", "log off"
- **System Info**: "system information", "cpu usage", "memory usage", "battery status", "check wifi"
- **Time and Date**: "what's the time", "what's the date"

### Media Commands
- **Volume Control**: "increase volume", "decrease volume", "mute volume", "set volume to 50 percent"
- **Brightness Control**: "increase brightness", "decrease brightness", "set brightness to 70 percent"
- **Media Playback**: "play", "pause", "next", "previous", "stop"

### YouTube and Web Commands
- **YouTube**: "play music on youtube", "search for cooking tutorials on youtube"
- **Specific Videos**: "play first video from search results", "play second video", "play third video from search results"
- **Web Searches**: "search for latest technology news", "google artificial intelligence"

### Information Requests
- **Weather**: "what's the weather", "weather in London"
- **News**: "show me the news", "get latest headlines"

### Other Features
- **Screenshots**: "take screenshot", "capture screen"

### Compound Commands
- **Multiple Actions**: "check the weather and play music on youtube"
- **Sequential Tasks**: "open chrome then search for programming tutorials"
- **Combined Operations**: "increase volume and take a screenshot"
- **Mixed Categories**: "what's the time and open calculator"

## AI Features

- **Command Learning**: The assistant learns from your commands over time
- **Confidence Scoring**: Shows confidence level for each command prediction
- **Sentiment Analysis**: Adjusts responses based on detected sentiment
- **Minimal Speech**: Reduced verbosity for a more efficient experience
- **Rule-Based Classification**: Directly matches common commands with high confidence
- **Machine Learning Classification**: Classifies unknown commands with confidence metrics
- **Compound Command Processing**: Separates and executes multiple commands in sequence

## Technical Details

### Command Processing Workflow
1. User speaks a command
2. Speech is converted to text via SpeechRecognition
3. The command is analyzed for conjunctions to identify compound commands
4. For compound commands, each part is processed sequentially
5. The AI Orchestrator analyzes each command and assigns a category and confidence score
6. Each command is processed by the appropriate module based on its category
7. Confidence score is displayed to inform the user about prediction certainty

### Module Descriptions
- **AI Orchestrator**: Central AI processing engine for command analysis
- **NLP Learning**: Natural language processing for command classification
- **Advanced Features**: Handles system operations, media control, and more
- **System Controls**: Manages applications, window states, and system functions
- **Web Search**: Handles web searches and YouTube integration
- **Speech Utils**: Manages speech recognition and text-to-speech

## Dependencies

Key dependencies include:
- SpeechRecognition: For voice command detection
- pyttsx3: For text-to-speech functionality
- pyautogui: For system control and screenshots
- psutil: For system information retrieval
- requests: For web API interactions
- wmi: For Windows system management (brightness control)
- BeautifulSoup4: For web content parsing
- pywin32: For Windows-specific controls

See requirements.txt for a complete list.

## Troubleshooting

- **Microphone issues**: Ensure your microphone is properly connected and enabled
- **Application opening issues**: Check that applications are installed in standard locations
- **Brightness control**: Requires administrative privileges on some systems and the WMI module
- **YouTube playback**: Relies on internet connectivity and a default browser
- **Low confidence commands**: If commands show low confidence scores (<0.4), try rephrasing
- **System info errors**: Ensure you have the required permissions for system information access
- **Compound commands**: If compound commands are not recognized correctly, try using clearer conjunctions like "and" or "then"

## Contributing

Feel free to submit issues and enhancement requests.

## License



