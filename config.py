# config.py
from langchain_ollama import ChatOllama
from laya import Router
from dotenv import load_dotenv
load_dotenv()
import os
from groq import Groq
from langchain_groq import ChatGroq





# Model names
SUPERVISOR_MODEL = "qwen3:4b"
AGENT_MODEL = "qwen3:4b"

# Retrieval settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 4

# Shared LLM instances

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
llm = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
router_llm = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# llm = ChatOllama(model=AGENT_MODEL, reasoning=False)

# router_llm = Router(preload=True)