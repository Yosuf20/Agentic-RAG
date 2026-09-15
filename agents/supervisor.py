from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict
from typing import Annotated



class State(TypedDict):
    messages : Annotated[list, add_messages]
    next : str
    done : bool

llm = ChatOllama(
    model="qwen3:4b",
    thinking=False,
)


def supervisor(state: State):

    query = state["messages"][-1].content

    prompt = """
You are a supervisor for a multi-agent system.

You have two agents:

1. pdf_agent:
   Use this when the user asks about information
   contained in the uploaded PDF.

2. web_agent:
   Use this when the user asks for current, external,
   or internet-based information.

3. done:
   Use this when the user's request has been completely
   answered and no more agent work is required.

User query:
{query}

Return ONLY one word:
pdf
web
done
"""

    response = llm.invoke(prompt)

    decision = response.content.strip().lower()
    print("Decision made by supervisor Agent--->s",decision)

    if "pdf" in decision:
        return {
            "next" : "pdf",
            "done" : False
        }

    elif "web" in decision:
        return {
            "next" : "webf",
            "done" : False
                }
    else:
        return {
            "done" : True
        }