from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

from graph.state import State

llm = ChatOllama(
    model="qwen3:4b",
)

def build_web_agent():
    print("Building Web Agent....")
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



