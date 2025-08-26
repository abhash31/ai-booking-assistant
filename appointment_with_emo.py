import os, time, threading, queue
import random
import pygame
from dataclasses import dataclass
from typing import Dict, List, Optional
from llama_index.embeddings.ollama import OllamaEmbedding
from booking_message import format_booking_message
from database.doctor_database import DoctorDB
from database.patient_database import BookingManager
from prompts import SYSTEM_PROMPT, chat_text_booking_prompt_str, chat_refine_booking_prompt_str
from regex import get_booking_data
from tts_stt.ai_voice_call import Piper
from vosk_test import VoskSpeech
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.chat_engine.types import ChatMode
from llama_index.llms.ollama import Ollama
from llama_index.core.prompts import RichPromptTemplate
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer

# ============ LLM CONFIG ============
Settings.embed_model = OllamaEmbedding(model_name='nomic-embed-text')

Settings.llm = Ollama(
    model="gemma3:4b",
    base_url="http://localhost:11434/",
    request_timeout=45.0,
    additional_kwargs={
        "num_ctx": 2048,
        "num_predict": 256,
        "temperature": 0.2,
        "thinking": {"enabled": False},
    },
)

# ============ RAG (Doctor's List) ============
docs = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(docs)
chat_store = SimpleChatStore()
chat_memory = ChatMemoryBuffer.from_defaults(token_limit=3000, chat_store=chat_store, chat_store_key="user1")



# ============ Chat Engine Setup ============
text_booking_template = RichPromptTemplate(chat_text_booking_prompt_str)
refine_template = RichPromptTemplate(chat_refine_booking_prompt_str)

chat_engine = index.as_chat_engine(
    memory=chat_memory,
    system_prompt=SYSTEM_PROMPT,
    similarity_top_k=4,
    chat_mode=ChatMode.CONTEXT,
    streaming=True,
)

# ============ Database Setup ============
# db = DoctorDB(); db.load_from_json_file('data/doctors_list.json')
# booking_manager = BookingManager()

# ============ Speech to Text and Text to Speech ============
tts = Piper('tts_stt/piper_tts_model/en_US-lessac-medium.onnx')
stt = VoskSpeech('tts_stt/vosk_stt_model/vosk-model-small-en-in-0.4')  # has start_listen/stop_listen

thinking_string = [
"Got it — let me check.",
"All right, let me see",
"On it—give me a moment.",
"Let me see what I can do.",
"Reviewing your request…",
"Working on this…",
"Thanks—working on it now.",
"Noted. I’m on it.",
"Just a moment while I check.",
"Let me grab those details…",
"Got it—working on this.",
]

# ================== UI  ==================
@dataclass
class UIState:
    emotion: str = "idle"
    text: str = ""
    running: bool = True

class EmotionDisplay:
    def __init__(self, emotion_root="emotions", fps=60, font_path=None, font_size=36, text_color=(255,255,255)):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # native fullscreen
        pygame.display.set_caption("Clinic Assistant")
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.font = pygame.font.Font(font_path, font_size)
        self.text_color = text_color
        self.emotion_root = emotion_root
        self.animations: Dict[str, List[pygame.Surface]] = {}
        self.frame_index = 0
        self.frame_timer = 0.0
        self.seconds_per_frame = 1.0 / 10.0  # 10fps per-emotion animation
        self.current_emotion = "idle"
        self._load_all()

        # text wrap area (80% screen width)
        self.max_text_width = int(self.screen.get_width() * 0.85)

    def _load_all(self):
        # Preload all emotions subfolders
        for emotion in os.listdir(self.emotion_root):
            folder = os.path.join(self.emotion_root, emotion)
            if not os.path.isdir(folder):
                continue
            frames = []
            for f in sorted(os.listdir(folder)):
                if not f.lower().endswith(".png"):
                    continue
                img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
                img = pygame.transform.smoothscale(img, self.screen.get_size())
                frames.append(img)
            if frames:
                self.animations[emotion] = frames
        if "idle" not in self.animations:
            raise RuntimeError("Missing 'idle' emotion folder with PNG frames.")

    def set_emotion(self, emotion: str):
        if emotion not in self.animations:
            emotion = "idle"
        if emotion != self.current_emotion:
            self.current_emotion = emotion
            self.frame_index = 0
            self.frame_timer = 0.0

    def wrap_lines(self, text: str) -> List[str]:
        if not text:
            return []
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            width, _ = self.font.size(test)
            if width <= self.max_text_width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        return lines[-8:]  # keep last few lines

    def draw(self, text: str):
        # background emotion frame
        frames = self.animations.get(self.current_emotion, self.animations["idle"])
        self.screen.blit(frames[self.frame_index], (0, 0))

        # overlay text (bottom-centered block)
        if text:
            lines = self.wrap_lines(text)
            h = self.screen.get_height()
            y = h - (len(lines) * (self.font.get_height() + 8)) - 40
            for line in lines:
                surf = self.font.render(line, True, self.text_color)
                rect = surf.get_rect(center=(self.screen.get_width() // 2, y))
                self.screen.blit(surf, rect)
                y += self.font.get_height() + 8

    def update(self, dt: float):
        # advance animation
        self.frame_timer += dt
        if self.frame_timer >= self.seconds_per_frame:
            self.frame_timer -= self.seconds_per_frame
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_emotion])

    def pump(self, ui: UIState):
        # handle events (must be in main thread)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ui.running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                ui.running = False
        self.set_emotion(ui.emotion)
        self.draw(ui.text)
        pygame.display.flip()
        self.update(self.clock.tick(self.fps) / 1000.0)

# ================== THREAD COMMUNICATION ==================
# Commands UI thread can receive
@dataclass
class UICommand:
    emotion: Optional[str] = None
    append_text: Optional[str] = None   # add tokens gradually
    set_text: Optional[str] = None      # overwrite
    clear_text: bool = False

# ================== APP CONTROLLER ==================
class App:
    def __init__(self):
        self.ui = UIState()
        self.display = EmotionDisplay(emotion_root="emotions", fps=60, font_size=40)

        self.cmd_q: "queue.Queue[UICommand]" = queue.Queue()
        self.worker = threading.Thread(target=self.conversation_loop, daemon=True)

    # ---- helpers to talk to UI (thread-safe) ----
    def ui_set_emotion(self, name: str):
        self.cmd_q.put(UICommand(emotion=name))

    def ui_set_text(self, text: str):
        self.cmd_q.put(UICommand(set_text=text))

    def ui_append_text(self, text: str):
        self.cmd_q.put(UICommand(append_text=text))

    def ui_clear(self):
        self.cmd_q.put(UICommand(clear_text=True))

    # ---- conversation orchestration in background ----
    def conversation_loop(self):
        # greeting (TTS blocks; keep mic muted)
        self.ui_set_emotion("idle")
        # stt.stop_listen()
        tts.get_and_speak("Hello! How can I help you?")   # Piper blocking speak method name may be .say or .speak
        time.sleep(0.15)

        while self.ui.running:
            # 1) LISTEN
            self.ui_set_emotion("idle")
            self.ui_set_text("")  # clear
            user_text = stt.get_text_from_speech()  # waits for speech + silence
            if not self.ui.running:
                break
            if not user_text:
                continue
            if user_text.strip().lower() in ("exit", "quit", "bye", "thank you"):
                self.ui_set_emotion("speaking")
                self.ui_set_text("Goodbye!")
                tts.get_and_speak("You are welcome! Have a nice day.")
                self.ui.running = False
                break

            # 2) THINK (LLM)
            self.ui_set_emotion("thinking")
            think = random.choice(thinking_string)
            tts.get_and_speak_non_blocking(f"You Said: {user_text}. {think}")
            self.ui_set_text(think)

            # Stream tokens so the screen updates live
            try:
                resp = chat_engine.stream_chat(user_text)  # returns StreamingAgentChatResponse
                answer = []
                self.ui_set_text("")
                for token in resp.response_gen:  # iterate the generator, not resp
                    answer.append(token)
                    self.ui_append_text(token)  # update your UI incrementally
                res_text = "".join(answer).strip().replace("*", "")
            except Exception as e:
                res_text = f"(error) {e}"
                self.ui_set_emotion("speaking")

            # 3) BOOK if confirmation present (your guard/regex)
            if "BOOKING_CONFIRMATION" in res_text:
                try:
                    data = get_booking_data(res_text)
                    booked = {
                        "patient": data["patient"],
                        "age": int(data["age"]),
                        "doctor": data["doctor"],
                        "date": data["date"],
                        "time": data["time"],
                    }
                    # booked = booking_manager.book_earliest(
                    #     patient_name=data["patient"],
                    #     patient_age=int(data["age"]),
                    #     doctor_name=data["doctor"],
                    #     date_str=data["date"],
                    #     time=data["time"],
                    # )
                    res_text = format_booking_message(booked)
                except Exception as e:
                    res_text = f"Booking error: {e}"
                    self.ui_set_emotion("error")

            # 4) SPEAK (and then go back to listening)
            self.ui_set_emotion("speaking")
            # Replace screen text with the final message (keeps it short if LLM rambled)
            self.ui_set_text(res_text)
            tts.get_and_speak(res_text)   # block; mic muted
            time.sleep(0.2)
            # stt.start_listen()
            self.ui_set_emotion("idle")
            # leave the last message on screen until next input

    # ---- main loop on the MAIN thread (required by pygame) ----
    def run(self):
        self.worker.start()
        last_text = ""
        while self.ui.running:
            # drain command queue → update UIState
            try:
                while True:
                    cmd: UICommand = self.cmd_q.get_nowait()
                    if cmd.clear_text: self.ui.text = ""
                    if cmd.set_text is not None: self.ui.text = cmd.set_text
                    if cmd.append_text is not None:
                        self.ui.text += cmd.append_text
                    if cmd.emotion is not None: self.ui.emotion = cmd.emotion
            except queue.Empty:
                pass

            self.display.pump(self.ui)

        pygame.quit()

if __name__ == "__main__":
    App().run()
