import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# ✅ FIX: proper static serving setup
app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)

UPLOAD_FOLDER = "pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory chat history (OK for demo, not production scale)
chat_histories = {}

def get_chat_history(session_id):
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    return chat_histories[session_id]


# =========================
# FRONTEND SERVING
# =========================

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# =========================
# HEALTH CHECK
# =========================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# =========================
# UPLOAD PDF
# =========================

@app.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        print("\n===== PDF UPLOAD REQUEST =====")

        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files allowed"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        print(f"Saved file: {filepath}")

        # Load PDF
        loader = PyMuPDFLoader(filepath)
        documents = loader.load()

        print(f"Loaded {len(documents)} pages")

        # Split text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(documents)

        print(f"Created {len(chunks)} chunks")

        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not set in environment variables")

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )

        # ✅ FIX: Render-safe storage path
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="/tmp/chroma_db"
        )

        print(f"Stored {len(chunks)} chunks in ChromaDB")

        return jsonify({
            "status": "ready",
            "chunks": len(chunks)
        })

    except Exception as e:
        import traceback
        print("UPLOAD ERROR TRACEBACK:")
        print(traceback.format_exc())

        return jsonify({"error": str(e)}), 500


# =========================
# ASK QUESTION (RAG)
# =========================

@app.route("/ask", methods=["POST"])
def ask():
    try:
        print("\n===== QUESTION REQUEST =====")

        data = request.get_json()
        question = data.get("question")
        session_id = data.get("session_id", "default")

        if not question:
            return jsonify({"error": "Question required"}), 400

        print(f"Session ID: {session_id}")
        print(f"Question: {question}")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not set in environment variables")

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )

        db = Chroma(
            persist_directory="/tmp/chroma_db",
            embedding_function=embeddings
        )

        retriever = db.as_retriever(search_kwargs={"k": 5})

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )

        # Chat history
        chat_history = get_chat_history(session_id)

        history_text = ""
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                history_text += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_text += f"Assistant: {msg.content}\n"

        # Rewrite question
        rewrite_prompt = f"""
Rewrite this question into a standalone question.

History:
{history_text}

Question:
{question}
"""

        standalone_question = llm.invoke(rewrite_prompt).content

        print("Standalone Question:", standalone_question)

        # Retrieve docs
        docs = retriever.invoke(standalone_question)

        print(f"Retrieved {len(docs)} chunks")

        context = "\n\n".join(doc.page_content for doc in docs)

        # Final prompt
        prompt = f"""
You are a helpful assistant answering based only on the document.

If answer not found, say:
Not found in document

Context:
{context}

Question:
{question}
"""

        response = llm.invoke(prompt)

        # Save memory
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response.content))

        sources = [
            {
                "page": doc.metadata.get("page", 0) + 1,
                "text": doc.page_content[:300]
            }
            for doc in docs
        ]

        return jsonify({
            "answer": response.content,
            "sources": sources
        })

    except Exception as e:
        import traceback
        print("ASK ERROR TRACEBACK:")
        print(traceback.format_exc())

        return jsonify({"error": str(e)}), 500


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)