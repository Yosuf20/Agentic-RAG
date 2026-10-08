from langchain_ollama import ChatOllama
import re

from graph.state import State

llm = ChatOllama(
    model="qwen3:4b",
    thinking=False,
    reasoning=False,
)

def supervisor(state: State):
    print("pdf_info in state:", repr(state.get("pdf_info")))

    pdf_info = state.get("pdf_info", "")
    pdf_section = (
        f"The user has uploaded a PDF: {pdf_info}"
        if pdf_info
        else "No PDF has been uploaded."
    )

    if not state.get("original_query"):
        original_query = state["messages"][-1].content
    else:
        original_query = state["original_query"]

    prompt = f"""/no_think
You are a supervisor for a multi-agent system.

{pdf_section}
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
{original_query}

Previous Agent result:
{state['messages']}

Return answer only in one word:
pdf,
web,
done
"""

    response = llm.invoke(prompt)


    decision_raw = response.content.strip().lower()
    print(decision_raw)

    # Strip out the <think>...</think> block entirely
    cleaned = re.sub(r"<think>.*?</think>", "", decision_raw, flags=re.DOTALL).strip()

    # Take only the last non-empty line — the model's real final answer
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    decision = lines[-1] if lines else cleaned

    print("****")
    print(decision)
    print("****")

    if decision == "pdf":
        return {
            "next" : "pdf",
            "done" : False
        }

    elif decision == "web":
        return {
            "next" : "web",
            "done" : False
                }
    else:
        return {
            "done" : True
        }