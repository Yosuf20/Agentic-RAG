from agents.pdfAgent import build_pdf_agent
from agents.webAgent import build_web_agent
from graph.workflow import build_workflow
from rag.pdf_processing import process_pdf
import streamlit as st



st.set_page_config(
    page_title="Multi-Agent RAG",
    page_icon="🤖",
    layout="wide"
)


def initialize_system(uploaded_file):

    filename = uploaded_file.name

    # Save uploaded PDF temporarily
    pdf_path = "temp.pdf"

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    

    # -------------------------
    # Retrievers
    # -------------------------
    pdf_info, retriever, bm25_retriever = process_pdf(pdf_path, filename)


    # -------------------------
    # Agents
    # -------------------------

    pdf_agent = build_pdf_agent(
        retriever,
        bm25_retriever
    )

    web_agent = build_web_agent()

    # -------------------------
    # Workflow
    # -------------------------

    graph = build_workflow(
        pdf_agent,
        web_agent
    )

    return graph, pdf_info


def main():

    st.title("🤖 Multi-Agent RAG")

    st.write(
        "Ask questions about your PDF or search the web "
        "using the multi-agent system."
    )

    # --------------------------------
    # Sidebar
    # --------------------------------

    with st.sidebar:

        st.header("📄 Upload PDF")

        uploaded_file = st.file_uploader(
            "Upload your PDF",
            type=["pdf"]
        )

        if uploaded_file:

            if st.button("Initialize System"):

                with st.spinner(
                    "Building RAG system..."
                ):

                    graph, pdf_info = initialize_system(
                        uploaded_file
                    )

                    st.session_state.graph = graph
                    st.session_state.pdf_info = pdf_info
                    st.session_state.initialized = True

                st.success("System ready!")

    # --------------------------------
    # Check initialization
    # --------------------------------

    if "initialized" not in st.session_state:

        st.info(
            "Upload a PDF and click "
            "'Initialize System' to begin."
        )

        return

    # --------------------------------
    # Chat Interface
    # --------------------------------

    st.subheader("💬 Ask a Question")

    query = st.chat_input(
        "Ask something about the PDF or the web..."
    )

    if query:

        # Display user message
        with st.chat_message("user"):
            st.write(query)

        # Run graph
        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                result = st.session_state.graph.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "pdf_info" : st.session_state.pdf_info,
                    }
                )

                response = result["messages"][-1].content

            st.write(response)


if __name__ == "__main__":
    main()