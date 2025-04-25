import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """Handles speech recognition functionality"""
    
    def __init__(self):
        """Initialize the speech recognizer"""
        self.recognizer = sr.Recognizer()
        # Adjust recognition parameters
        self.recognizer.energy_threshold = 300  # Minimum audio energy to consider for recording
        self.recognizer.dynamic_energy_threshold = True  # Automatically adjust for ambient noise
        self.recognizer.pause_threshold = 0.5  # Seconds of non-speaking audio before a phrase is considered complete
        self.recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speaking audio a phrase
        self.recognizer.non_speaking_duration = 0.3  # Seconds of non-speaking audio to keep on both sides of the recording
        
    def listen(self, timeout=5):
        """
        Listen for speech and convert to text
        
        Args:
            timeout (int): Number of seconds to listen for
            
        Returns:
            str: Recognized text, or None if recognition fails
        """
        try:
            # Create a new microphone instance
            microphone = sr.Microphone()
            
            with microphone as source:
                logger.info("Adjusting for ambient noise...")
                # Quick ambient noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                logger.info("Listening for speech...")
                try:
                    # Listen for audio input
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
                    logger.info("Audio captured, starting recognition...")
                    
                    # Try to recognize the speech
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    logger.info(f"Successfully recognized: {text}")
                    return text
                    
                except sr.WaitTimeoutError:
                    logger.info("No speech detected within timeout period")
                    return None
                    
        except sr.UnknownValueError:
            logger.info("Speech was unintelligible")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return None 