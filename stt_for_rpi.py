# vosk_auto.py
import json
import time
import audioop
import pyaudio
from vosk import Model, KaldiRecognizer

class VoskSpeech:
    """
    - Auto-picks a usable input device (no manual device name).
    - Uses the device's native sample rate; resamples to 16kHz for Vosk if needed.
    - Blocks until speech + trailing silence (like your mac version).
    """

    def __init__(self, path_to_model: str, prefer_rate: int = 16000):
        self.model = Model(path_to_model)
        self.pa = pyaudio.PyAudio()
        self.rec_rate = prefer_rate  # Vosk model rate (16k typical)
        self.device_index, self.device_rate = self._auto_pick_device()
        self.recognizer = KaldiRecognizer(self.model, self.rec_rate)

    # ----- device selection -----
    def _auto_pick_device(self):
        """Choose default input device if available; otherwise best candidate."""
        # 1) Try default input
        try:
            info = self.pa.get_default_input_device_info()
            if info and int(info.get("maxInputChannels", 0)) > 0:
                return int(info["index"]), int(info.get("defaultSampleRate", 16000))
        except OSError:
            pass  # no default device on this backend

        # 2) Fallback: first good input, but avoid “monitor/loopback/output”
        candidates = []
        for i in range(self.pa.get_device_count()):
            inf = self.pa.get_device_info_by_index(i)
            if int(inf.get("maxInputChannels", 0)) <= 0:
                continue
            candidates.append(inf)

        if not candidates:
            raise RuntimeError("No input device with maxInputChannels > 0 was found.")

        def score(inf):
            name = inf.get("name", "").lower()
            # penalize non-mics
            s = 0
            if "monitor" in name or "loopback" in name or "output" in name:
                s -= 5
            # prefer rates near 16k
            rate = int(inf.get("defaultSampleRate", 16000))
            s -= abs(rate - self.rec_rate) / 1000.0
            # a touch of preference for more input channels (often 1 or 2)
            s += float(inf.get("maxInputChannels", 1)) * 0.1
            return s

        best = max(candidates, key=score)
        return int(best["index"]), int(best.get("defaultSampleRate", 16000))

    # ----- main capture with resampling & silence tail -----
    def get_text_from_speech(self, silence_timeout: float = 1.0, max_duration: float = 10.0) -> str:
        """
        Listen until speech occurs, then stop after 'silence_timeout' seconds of trailing silence.
        Also stops after 'max_duration' seconds total.
        """
        # ~20ms frames are stable across devices
        frames_per_buffer = max(256, int(self.device_rate * 0.02))

        stream = self.pa.open(
            rate=self.device_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=frames_per_buffer,
        )
        stream.start_stream()
        print(f"Listening on device #{self.device_index} at {self.device_rate} Hz...")

        start_time = time.time()
        last_speech_time = None
        full_text = ""
        rs_state = None  # audioop.ratecv state

        try:
            while True:
                data = stream.read(frames_per_buffer, exception_on_overflow=False)

                # resample to recognizer rate if needed
                if self.device_rate != self.rec_rate:
                    data, rs_state = audioop.ratecv(
                        data, 2, 1, self.device_rate, self.rec_rate, rs_state
                    )

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if result.get("text"):
                        full_text += " " + result["text"]
                        last_speech_time = time.time()
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get("partial"):
                        last_speech_time = time.time()

                # only consider silence if we've heard speech
                if last_speech_time and (time.time() - last_speech_time > silence_timeout):
                    print("Silence detected, stopping...")
                    break

                if time.time() - start_time > max_duration:
                    print("Max duration reached, stopping...")
                    break
        finally:
            stream.stop_stream()
            stream.close()

        return full_text.strip()


# No manual device name needed
stt = VoskSpeech("tts_stt/vosk_stt_model/vosk-model-small-en-in-0.4")

# print("Recognized:", stt.get_text_from_speech(
#     silence_timeout=1.0,   # increase to ~1.2–1.5 if it cuts off too fast
#     max_duration=12.0
# ))
