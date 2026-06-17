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

from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

load_dotenv()

app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)

UPLOAD_FOLDER = "pdfs"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

# Session memory storage
chat_histories = {}


def get_chat_history(session_id):

    if session_id not in chat_histories:

        chat_histories[session_id] = []

    return chat_histories[session_id]


    
@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.route("/health", methods=["GET"])
def health():

    return jsonify(
        {
            "status": "ok"
        }
    )


@app.route("/upload", methods=["POST"])
def upload_pdf():

    print("\n===== PDF UPLOAD REQUEST =====")

    if "file" not in request.files:

        return jsonify(
            {
                "error":
                "No file uploaded"
            }
        ), 400

    file = request.files["file"]

    if file.filename == "":

        return jsonify(
            {
                "error":
                "No file selected"
            }
        ), 400

    if not file.filename.lower().endswith(".pdf"):

        return jsonify(
            {
                "error":
                "Only PDF files allowed"
            }
        ), 400

    filepath = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(filepath)

    print(
        f"Saved file: {filepath}"
    )

    try:

        loader = PyMuPDFLoader(
            filepath
        )

        documents = loader.load()

        print(
            f"Loaded {len(documents)} pages"
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
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

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )

        print(
            f"Stored {len(chunks)} chunks in ChromaDB"
        )

        return jsonify(
            {
                "status": "ready",
                "chunks": len(chunks)
            }
        )

    except Exception as e:

        print("UPLOAD ERROR:", str(e))

        return jsonify(
            {
                "error": str(e)
            }
        ), 500


@app.route("/ask", methods=["POST"])
def ask():

    try:

        print("\n===== QUESTION REQUEST =====")

        data = request.get_json()

        question = data.get(
            "question"
        )

        session_id = data.get(
            "session_id",
            "default"
        )

        if not question:

            return jsonify(
                {
                    "error":
                    "Question required"
                }
            ), 400

        print(
            f"Session ID: {session_id}"
        )

        print(
            f"Question: {question}"
        )

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv(
                "GEMINI_API_KEY"
            )
        )

        db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings
        )

        retriever = db.as_retriever(
            search_kwargs={"k": 10}
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv(
                "GEMINI_API_KEY"
            )
        )

        # Load chat history

        chat_history = get_chat_history(
            session_id
        )

        history_text = ""

        for msg in chat_history:

            if isinstance(
                msg,
                HumanMessage
            ):

                history_text += (
                    f"User: {msg.content}\n"
                )

            elif isinstance(
                msg,
                AIMessage
            ):

                history_text += (
                    f"Assistant: {msg.content}\n"
                )

        print("\n===== CHAT HISTORY =====")
        print(history_text)

        # Rewrite follow-up question

        rewrite_prompt = f"""
Given the chat history and latest question,
rewrite the latest question so it is fully standalone.

History:
{history_text}

Question:
{question}
"""

        standalone_question = (
            llm.invoke(
                rewrite_prompt
            ).content
        )

        print(
            "\nStandalone Question:"
        )
        print(
            standalone_question
        )

        # Retrieve documents

        docs = retriever.invoke(
            standalone_question
        )

        print(
        f"\nRetrieved {len(docs)} chunks"
        )

        for i, doc in enumerate(docs):
            print(f"\n===== CHUNK {i+1} =====")
            print(doc.page_content[:500])

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )
        
        print("\n===== CONTEXT SENT TO GEMINI =====")
        print(context[:3000])

        # Final RAG prompt

        prompt = f"""
You are answering questions about the uploaded PDF.

Use ONLY information from the context.

If the context contains enough information,
answer clearly and briefly.

If the answer cannot be found in the context,
respond exactly:

Not found in document

Chat History:
{history_text}

Context:
{context}

Question:
{question}
"""

        response = llm.invoke(
            prompt
        )

        print(
            "\n===== ANSWER ====="
        )

        print(
            response.content
        )

        # Save memory

        chat_history.append(
            HumanMessage(
                content=question
            )
        )

        chat_history.append(
            AIMessage(
                content=response.content
            )
        )

        print(
            f"\nMessages Stored: {len(chat_history)}"
        )

        sources = []

        for doc in docs:

            sources.append(
                {
                    "page":
                    doc.metadata.get(
                        "page",
                        0
                    )+1,

                    "text":
                    doc.page_content[:300]
                }
            )

        return jsonify(
            {
                "answer":
                response.content,

                "sources":
                sources
            }
        )

    except Exception as e:

        print(
            "ASK ERROR:",
            str(e)
        )

        return jsonify(
            {
                "error":
                str(e)
            }
        ), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )