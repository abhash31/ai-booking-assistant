# import speech_recognition as sr
# import pyttsx3
import simpleaudio as sa


import threading
import wave
from piper import PiperVoice
from pydub import AudioSegment
from pydub.playback import play

class Piper:
    def __init__(self, path_to_model):
        self.voice = PiperVoice.load(path_to_model)

    def get_and_speak(self, text):
        with wave.open("test.wav", "wb") as wav_file:
            self.voice.synthesize_wav(text, wav_file)

        # sound = AudioSegment.from_wav('test.wav')
        # play(sound)
        wave_obj = sa.WaveObject.from_wave_file('test.wav')
        play_obj = wave_obj.play()
        play_obj.wait_done()  # wait until playback finishes
        # play_obj.stop()

    def get_and_speak_non_blocking(self, text):
    # This method runs the speech synthesis and playback in a separate thread.
        threading.Thread(target=self.get_and_speak, args=(text,)).start()