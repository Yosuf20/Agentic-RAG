from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from typing_extensions import TypedDict
from rag.vectordb import hybrid_retrieve 
from tools.pdf_search import create_pdf_search_tool
from typing import Annotated






class State(TypedDict):
    messages : Annotated[list, add_messages]


llm = ChatOllama(
    model="qwen3:4b"
)




def build_pdf_agent(vector_retriever, bm25_retriever):
    print("Building Pdf Agent....")

    # Create PDF search tool using the retrievers
    search_pdf = create_pdf_search_tool(
        vector_retriever,
        bm25_retriever
    )

    tools = [search_pdf]

    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):

        response = llm_with_tools.invoke(
            state["messages"]
        )

        return {
            "messages": [response]
        }

    # Build graph
    graph_builder = StateGraph(State)

    graph_builder.add_node("main_llm",chatbot)

    graph_builder.add_node("tools",ToolNode(tools))

    graph_builder.add_edge(START,"main_llm")

    graph_builder.add_conditional_edges("main_llm",tools_condition)

    graph_builder.add_edge("tools","main_llm")

    return graph_builder.compile()