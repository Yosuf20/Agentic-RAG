from langchain_core.tools import tool

from rag.vectordb import hybrid_retrieve

def create_pdf_search_tool(vector_retriever, bm25_retriever):

    @tool
    def search_pdf(query: str) -> str:
        """
        Search the uploaded PDF for information relevant to the user's query.

        Use this tool when the user asks a question that requires
        information from the uploaded PDF.
        """

        docs = hybrid_retrieve(
            query,
            vector_retriever,
            bm25_retriever
        )

        if not docs:
            return "No relevant information was found in the PDF."

        return "\n\n".join(
            doc.page_content
            for doc in docs
        )

    return search_pdf