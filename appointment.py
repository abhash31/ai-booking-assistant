import textwrap
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from booking_message import format_booking_message
from database.doctor_database import DoctorDB
from database.patient_database import BookingManager
from prompts import *
from regex import get_booking_data
from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine.types import ChatMode
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.prompts import RichPromptTemplate
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.google_genai import GoogleGenAI
from tts_stt.ai_voice_call import Piper
from vosk_test import VoskSpeech

# embedding model *required for document related queries for proper formatting of data
# Settings.embed_model = GoogleGenAIEmbedding(
#     model_name="models/embedding-001", api_key=os.environ["GOOGLE_API_KEY"]
# )
Settings.embed_model = OllamaEmbedding(model_name='nomic-embed-text')

# Settings.llm = GoogleGenAI(api_key=os.environ["GOOGLE_API_KEY"], temperature=0)

Settings.llm = Ollama(
    model="gemma3:4b",
    context_window=8192,
    temperature=0.0,
    request_timeout=30.0,
    thinking=False
)

# Settings.llm = Ollama(
#     model="deepseek-r1:1.5b",
#     context_window=8192,
#     temperature=0.6,
#
#     request_timeout=30.0,
#     thinking=False
# )

# tts class init *for voice input and outputs
tts = Piper('tts_stt/piper_tts_model/en_US-lessac-medium.onnx')
stt = VoskSpeech('tts_stt/vosk_stt_model/vosk-model-small-en-in-0.4')

# chat store setup *for chat history (memory) management
chat_store = SimpleChatStore()
chat_memory = ChatMemoryBuffer.from_defaults(
    token_limit=3000,
    chat_store=chat_store,
    chat_store_key="user1",
)

# document loading
# documents = SimpleDirectoryReader("data").load_data()
#
# # indexing the document
# index = VectorStoreIndex.from_documents(documents)

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

documents = SimpleDirectoryReader("data").load_data()
nodes = splitter.get_nodes_from_documents(documents)

index = VectorStoreIndex(nodes)

# formatting prompt as template
text_booking_template = RichPromptTemplate(chat_text_booking_prompt_str)
refine_template = RichPromptTemplate(chat_refine_booking_prompt_str)

db = DoctorDB()
db.load_from_json_file('data/doctors_list.json')
booking_manager = BookingManager()

# chat engine setup
chat_engine = index.as_chat_engine(
    memory=chat_memory,
    system_prompt=SYSTEM_PROMPT,
    # text_qa_template=text_booking_template,
    # refine_template=refine_template,
    similarity_top_k=4,
    chat_mode=ChatMode.CONTEXT,
)

# chat interface
def chat_with_gemini():
    # print(booking_manager.get_everything())
    print("Bot: Hello! How can we help you?")
    # tts.get_and_speak("Hello! How can we help you?")
    while True:
        try:
            # aud = tts.listen_speech()
            # speech_txt = tts.speech_to_text(aud)
            # user_input = stt.get_text_from_speech()
            # # print(user_input)
            # prompt = SYSTEM_PROMPT
            user_input = input("input: ")
            # user_input = prompt + "\n" + user_input
            # print(f"input: {user_input}")
            if user_input.lower() == 'exit' or 'thank you' in user_input.lower():
                # tts.get_and_speak("You are welcome! Have a nice day.")
                print("Bot: Goodbye!")
                break
            elif user_input == 'error':
                print("couldn't hear that")
                # tts.get_and_speak("Didn't catch you there. Can you say it again?")
            else:
                # tts.get_and_speak_non_blocking(f"You Said: {user_input}")
                response = chat_engine.chat(user_input, )
                # print("here2")
                history = chat_store.get_messages("user1")
                res_text = response.response.strip().replace("*", "")
                if "BOOKING_CONFIRMATION" in res_text:
                    # format booking data
                    booking_data = get_booking_data(res_text)
                    print(booking_data['date'])

                    # book data
                    final_data = booking_manager.book_earliest(patient_name=booking_data['patient'],
                                                               patient_age=int(booking_data['age']),
                                                               doctor_name=booking_data['doctor'],
                                                               date_str=booking_data['date'],
                                                               time=booking_data['time'])

                    res_text = format_booking_message(final_data)
                    # history.pop()

                # print(history)
                history.pop()
                history.append(ChatMessage(role = 'assistant', content=res_text))
                chat_store.set_messages("user1", history)
                wrapped_text = textwrap.fill(res_text, width=100)
                print("Bot:", wrapped_text)
                # tts.get_and_speak(res_text)
                # print("Bot:", response.response.strip())
                # print(booking_manager.list_bookings_for_day())
                chat_store.persist(persist_path="chat_store.json")
        except Exception as e:
            print(f"couldn't hear that {e}")
            # tts.get_and_speak("Didn't catch you there. Can you say it again?")

chat_with_gemini()
