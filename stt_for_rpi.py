import time
import speech_recognition as sr

class SpeechRecognitionGoogle:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def get_text_from_speech(self, silence_timeout=1.0, max_duration=15.0):
        with self.microphone as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            print("Listening... Speak now.")
            start_time = time.time()
            audio_data = None

            try:
                audio_data = self.recognizer.listen(source, timeout=max_duration, phrase_time_limit=max_duration)
            except sr.WaitTimeoutError:
                print("No speech detected within time limit.")
                return ""

        try:
            text = self.recognizer.recognize_google(audio_data)
            return text.strip()
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"API error: {e}")
            return ""

# Example usage:
# recognizer = SpeechRecognitionGoogle()
# print("Recognized:", recognizer.get_text_from_speech())