import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

loader = PyMuPDFLoader(
    "pdfs/sample.pdf"
)

documents = loader.load()

print(
    f"Loaded {len(documents)} pages"
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_documents(
    documents
)

print(
    f"Created {len(chunks)} chunks"
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv(
        "GEMINI_API_KEY"
    )
)

vectorstore =Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print(
    f"{len(chunks)} chunks stored"
)