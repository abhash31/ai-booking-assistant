from langchain_community.llms.llamacpp import LlamaCpp
from llama_index.llms.ollama import Ollama

llm = Ollama(
    model="gemma3:4b",
    base_url="http://3.110.191.4:11434",
    request_timeout=120.0,
    context_window=8000,
)

# llm = LlamaCpp(model_path="gemma-3-270m-it-IQ4_NL.gguf",
# temperature=0.1)
#
resp = llm.complete("Who are you and what can you do?")

print(resp)