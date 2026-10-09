# config.py
from langchain_ollama import ChatOllama
from laya import Router
from dotenv import load_dotenv
load_dotenv()
import os

from langchain_groq import ChatGroq
llm = ChatGroq(model= "openai/gpt-oss-20b", temperature=0)
router_llm = llm



# Model names
SUPERVISOR_MODEL = "qwen3:4b"
AGENT_MODEL = "qwen3:4b"

# Retrieval settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 4

# # Shared LLM instances
# llm = ChatOllama(model=AGENT_MODEL, reasoning=False)
# router_llm = Router(preload=True)