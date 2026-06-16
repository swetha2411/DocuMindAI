import os

from dotenv import load_dotenv

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

from langchain_community.vectorstores import Chroma

load_dotenv()

# Embedding model
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Load ChromaDB
db = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# Retriever
retriever = db.as_retriever(
    search_kwargs={"k": 4}
)

# Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Question
query = "What is self-attention?"

# Retrieve relevant chunks
docs = retriever.invoke(query)

# Combine retrieved chunks into context
context = "\n\n".join(
    doc.page_content for doc in docs
)

# RAG Prompt
prompt = f"""
You are a helpful assistant.

Answer ONLY from the context below.

If the answer is not present in the context,
say "Not found in document".

Context:
{context}

Question:
{query}
"""

# Generate answer
response = llm.invoke(prompt)

print("\nQUESTION:")
print(query)

print("\nANSWER:")
print(response.content)

print("\nSOURCE CHUNKS USED:")

for i, doc in enumerate(docs, start=1):
    print(f"\nSource {i}")
    print("-" * 50)
    print(doc.page_content[:500])