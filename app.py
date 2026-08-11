from rag.loader import load_pdf
from rag.spliiter import doc_spliiter
from rag.encoder import get_embeddings
from rag.vectordb import get_retreivers, vector_db
from agents.pdfAgent import build_pdf_agent
from agents.webAgent import build_web_agent
from graph.workflow import build_workflow
import streamlit as st


# path = r"C:\Users\Yosuf Jamal\OneDrive\Desktop\Intern Projects\encoder-decoder-paper.pdf"

# def main():

#     content = load_pdf(path)

#     print(type(content))
#     print("*"*50)
#     print(len((content[0]).page_content))

#     chunks = doc_spliiter(content=content)

#     embeding_model = get_embeddings()

#     vector_store = vector_db(chunks, embeding_model)

#     vector_retriver , bm25retriever = get_retreivers(chunks, vector_store)

#     pdf_agent = build_pdf_agent(
#         vector_retriever=vector_retriver,
#         bm25_retriever=bm25retriever)

#     web_agent = build_web_agent()

#     graph = build_workflow(pdf_agent, web_agent)

#     query = input("Ask a Question: \n")

#     result = graph.invoke({
#         "messages" : [
#             {
#                 "role" : "user",
#                 "content" : query
#             }
#         ]
#     })

#     print("\nResult:")
#     print(result["messages"][-1].content)

# if __name__ == "__main__":
#     main()



st.set_page_config(
    page_title="Multi-Agent RAG",
    page_icon="🤖",
    layout="wide"
)


def initialize_system(uploaded_file):

    # Save uploaded PDF temporarily
    pdf_path = "temp.pdf"

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # -------------------------
    # PDF Loading
    # -------------------------

    content = load_pdf(pdf_path)

    # -------------------------
    # Splitting
    # -------------------------

    chunks = doc_spliiter(content)

    # -------------------------
    # Embeddings
    # -------------------------

    embeddings = get_embeddings()

    # -------------------------
    # Vector Database
    # -------------------------

    vector_store = vector_db(
        chunks,
        embeddings 
    )

    # -------------------------
    # Retrievers
    # -------------------------

    vector_retriever, bm25_retriever = get_retreivers(
        chunks,
        vector_store
    )

    # -------------------------
    # Agents
    # -------------------------

    pdf_agent = build_pdf_agent(
        vector_retriever,
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

    return graph


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

                    graph = initialize_system(
                        uploaded_file
                    )

                    st.session_state.graph = graph
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
                        ]
                    }
                )

                response = result["messages"][-1].content

            st.write(response)


if __name__ == "__main__":
    main()