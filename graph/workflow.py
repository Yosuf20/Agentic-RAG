from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from typing_extensions import TypedDict
from typing import Annotated
from agents.supervisor import supervisor


class State(TypedDict):
    messages : Annotated[list, add_messages]
    next : str
    done : bool



def route_supervisor(state):

    if state.get("done"):
        return END
    if state["next"] == "pdf":
        print("Called Pdf Agent")
        return "Pdf_Agent"
    elif state["next"] == "web":
        print("Called Web Agent")
        return "Web_Agent"

    


def build_workflow(pdf_agent, web_agent):

    Graph_builder = StateGraph(State)

    Graph_builder.add_node("Pdf_Agent", pdf_agent)
    Graph_builder.add_node("Web_Agent", web_agent)
    Graph_builder.add_node("Supervisor", supervisor)

    Graph_builder.add_edge(START, "Supervisor")

    Graph_builder.add_conditional_edges(
        "Supervisor",
        route_supervisor,
        {
            "Pdf_Agent" : "Pdf_Agent",
            "Web_Agent" : "Web_Agent",
            END : END
        }
    )
        

    Graph_builder.add_edge("Pdf_Agent", "Supervisor")
    Graph_builder.add_edge("Web_Agent", "Supervisor")

    return Graph_builder.compile() 


