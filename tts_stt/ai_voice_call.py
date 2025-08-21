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

# pipe = Piper('../en_US-lessac-medium.onnx')
#
# print("1")
# pipe.get_and_speak("what up dawg!")
# print("2")


# def speak_text(command):
#     engine = pyttsx3.init() # tts init
#     engine.say(command)
#     engine.runAndWait()
#
# import threading
#
# def speak_text_async(text: str):
#     """Run speak_text in a background thread so it doesn’t block."""
#     t = threading.Thread(target=speak_text, args=(text,), daemon=True)
#     t.start()
#
# class TextToSpeechToText:
#     def __init__(self):
#         self.recognizer = sr.Recognizer()
#         # r = sr.Recognizer() # speech recognizer
#
#     def listen_speech(self):
#         try:
#             with sr.Microphone() as source2:  # microphone as source for input
#
#                 print("listening..start")
#
#                 self.recognizer.adjust_for_ambient_noise(source2, duration=0.2)  # ambient adjustment
#
#                 self.recognizer.pause_threshold = 1 # pause threshold
#
#                 audio2 = self.recognizer.listen(source2)  # listens for the user's input
#
#                 print("listening..stop")
#
#                 return audio2 # return audio
#
#         except:
#             print("try again")
#             return "error"
#
#     def speech_to_text(self, speech):
#         try:
#             speech_text = self.recognizer.recognize_google(speech) # google to recognize audio
#             speech_text = speech_text.lower()
#             return speech_text # return text
#         except:
#             return "error"
