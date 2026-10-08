from langchain_ollama import ChatOllama
from concurrent.futures import ThreadPoolExecutor
import re
from rag.loader import load_pdf              # your real names here
from rag.spliiter import doc_spliiter
from rag.encoder import get_embeddings
from rag.vectordb import vector_db, get_retreivers, hybrid_retrieve
from config import llm

def summarize_pdf(docs, filename: str) -> str:
    # first few pages are enough to identify the document type
    sample = "\n".join(d.page_content for d in docs[:3])[:3000]

    prompt = f"""/no_think
Here is the beginning of a PDF named "{filename}":

{sample}

In 2 sentences, state what kind of document this is (resume, invoice,
research paper, contract, etc.) and its main topic. Output only those sentences."""

    raw = llm.invoke(prompt).content
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return f"{filename}: {cleaned}"

def _build_retriever(chunks):
    embeddings = get_embeddings()
    vectorstore = vector_db(chunks, embeddings)
    return get_retreivers(chunks, vectorstore)

def process_pdf(path, filename):
    docs = load_pdf(path)
    chunks = doc_spliiter(docs)

    with ThreadPoolExecutor(max_workers=2) as pool:
        summary_future = pool.submit(summarize_pdf, llm, docs, filename)
        retriever_future = pool.submit(_build_retriever, chunks)

        try:
            pdf_info = summary_future.result()
        except Exception:
            pdf_info = f"{filename}: (summary unavailable)"

        retriever, bm25_retriever = retriever_future.result()

    return pdf_info, retriever, bm25_retriever