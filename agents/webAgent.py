from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict
from typing import Annotated
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()


class State(TypedDict):
    messages : Annotated[list, add_messages]

llm = ChatOllama(
    model="qwen3:4b",
)

def build_web_agent():
    tool = TavilySearch(max_results=2)
    tools = [tool]

    llm_with_tools = llm.bind_tools(tools)



    def chatbot(state: State):
        responce = llm_with_tools.invoke(state["messages"])

        return {
            "messages": [responce]
            }

    
    Graph_builder = StateGraph(State)
    Graph_builder.add_node("main_llm", chatbot)
    Graph_builder.add_node("tools", ToolNode(tools=tools))

    Graph_builder.add_edge(START,"main_llm")
    Graph_builder.add_conditional_edges(
    "main_llm",

    tools_condition
    )

    Graph_builder.add_edge("tools", 'main_llm')

    Graph = Graph_builder.compile()

    return Graph



