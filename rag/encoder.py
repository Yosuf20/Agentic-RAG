from sentence_transformers import SentenceTransformer
import numpy as np 
from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings():
    print("3.Started Loading Sentence Transformer")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )
    print("Done loading model")
    return embeddings