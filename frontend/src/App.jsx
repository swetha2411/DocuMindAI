import { useState } from "react";
import axios from "axios";

import UploadPanel from "./components/UploadPanel";
import ChatWindow from "./components/ChatWindow";
import MessageInput from "./components/MessageInput";

import "./App.css";

function App() {

  const [messages, setMessages] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [pdfReady, setPdfReady] =
    useState(false);

  const [sessionId, setSessionId] =
    useState(crypto.randomUUID());

  const handleSend = async (
    question
  ) => {

    try {

      setMessages(prev => [
        ...prev,
        {
          sender: "user",
          text: question
        }
      ]);

      setLoading(true);

      const response =
        await axios.post(
          `${import.meta.env.VITE_API_URL}/ask`,
          {
            session_id: sessionId,
            question
          }
        );

      setMessages(prev => [
        ...prev,
        {
          sender: "bot",
          text:
            response.data.answer,
          sources:
            response.data.sources
        }
      ]);

    } catch (error) {

      console.error(error);

      setMessages(prev => [
        ...prev,
        {
          sender: "bot",
          text:
            "Error generating answer."
        }
      ]);

    } finally {

      setLoading(false);

    }
  };

  const clearChat = () => {

    setMessages([]);

    setSessionId(
      crypto.randomUUID()
    );

  };

  return (
    <div className="app">

      <h1>DocuMind AI</h1>

      <UploadPanel
        onReady={() =>
          setPdfReady(true)
        }
      />

      {pdfReady && (
        <>
          <ChatWindow
            messages={messages}
          />

          <MessageInput
            onSend={handleSend}
            loading={loading}
          />

          <button
            className="clear-btn"
            onClick={clearChat}
          >
            Clear Chat
          </button>
        </>
      )}

    </div>
  );
}

export default App;