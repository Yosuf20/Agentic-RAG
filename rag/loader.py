from langchain_community.document_loaders import PyMuPDFLoader

def load_pdf(path):
    loader = PyMuPDFLoader(path)
    print("1.Loading Pdf....")
    return loader.load()