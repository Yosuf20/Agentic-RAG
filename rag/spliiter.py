from langchain_text_splitters import RecursiveCharacterTextSplitter

def doc_spliiter(content):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(content)

    return chunks