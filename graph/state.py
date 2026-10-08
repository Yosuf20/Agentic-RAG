# graph/state.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    original_query: str
    pdf_info: str
    next: str
    done: bool