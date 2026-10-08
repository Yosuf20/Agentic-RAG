# config.py
from langchain_ollama import ChatOllama

# Model names
SUPERVISOR_MODEL = "qwen3:4b"
AGENT_MODEL = "qwen3:4b"

# Retrieval settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 4

# Shared LLM instances
llm = ChatOllama(model=AGENT_MODEL, reasoning=False)
router_llm = ChatOllama(model=SUPERVISOR_MODEL, reasoning=False, temperature=0)