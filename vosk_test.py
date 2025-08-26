import json
import time
import pyaudio
from vosk import Model, KaldiRecognizer

class VoskSpeech:
    def __init__(self, path_to_model):
        model = Model(path_to_model)
        self.recognizer = KaldiRecognizer(model, 16000)
        self.mic = pyaudio.PyAudio()

    def get_text_from_speech(self, silence_timeout=1.0, max_duration=10.0):
        stream = self.mic.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=4096)
        stream.start_stream()

        print("Listening... Speak now.")

        start_time = time.time()
        last_speech_time = None  # Don't set until we actually hear speech
        full_text = ""

        while True:
            data = stream.read(4096, exception_on_overflow=False)

            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result.get("text"):
                    full_text += " " + result["text"]
                    last_speech_time = time.time()  # Set only after actual speech
            else:
                partial = json.loads(self.recognizer.PartialResult())
                if partial.get("partial"):
                    last_speech_time = time.time()

            # Don't stop for silence unless speech has started
            if last_speech_time:
                if time.time() - last_speech_time > silence_timeout:
                    print("Silence detected, stopping...")
                    break

            # Optional: prevent endless recording
            if time.time() - start_time > max_duration:
                print("Max duration reached, stopping...")
                break

        stream.stop_stream()
        stream.close()

        return full_text.strip()

# Example usage:
recognizer = VoskSpeech("tts_stt/vosk_stt_model/vosk-model-small-en-in-0.4")
print("Recognized:", recognizer.get_text_from_speech())
