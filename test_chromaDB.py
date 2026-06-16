import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

documents = [
    "AgroSmart offers crop disease detection.",
    "The pricing plan starts at 499 rupees per month.",
    "Farmers can upload images for analysis.",
    "Weather forecasts are updated every hour.",
    "Premium users receive detailed reports."
]

vectorstore = Chroma.from_texts(
    texts=documents,
    embedding=embeddings,
    persist_directory="chroma_db"
)

query = "what does the system say about pricing?"

results = vectorstore.similarity_search(query, k=1)

print(results[0].page_content)