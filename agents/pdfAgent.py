from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_ollama import ChatOllama
from tools.pdf_search import create_pdf_search_tool

from graph.state import State
from config import llm


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