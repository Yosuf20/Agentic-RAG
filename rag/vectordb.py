from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever


def vector_db(chunks, embeddings):
    print("Creating Vector Store")
    vector_store = FAISS.from_documents(
            embedding = embeddings,
            documents= chunks
        )
    print("Done Creating Vector Store")
    return vector_store

def get_retreivers(chunks, vector_store):
    print("Making Retriver")
    retriever = vector_store.as_retriever(
        search_type='mmr',
        search_kwargs={'k':4}
    )
    bm25_retriever = BM25Retriever.from_documents(chunks)

    return retriever, bm25_retriever


def hybrid_retrieve(query, retriever, bm25_retriever):
    print("Making Hybrid Retriver")
        
    vector_docs = retriever.invoke(query)
    bm25_docs = bm25_retriever.invoke(query)

    # Keep FAISS results first
    
    combined = vector_docs.copy()

    seen = {doc.page_content for doc in combined}

    for doc in bm25_docs:
        if doc.page_content not in seen:
            combined.append(doc)
            seen.add(doc.page_content)

    return combined[:4]