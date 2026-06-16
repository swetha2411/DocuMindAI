import { useState } from "react";

function MessageInput({
  onSend,
  loading
}) {

  const [question, setQuestion] =
    useState("");

  const handleSend = () => {

    if (!question.trim())
      return;

    onSend(question);

    setQuestion("");
  };

  return (
    <div className="message-input">

      <input
        type="text"
        value={question}
        placeholder="Ask a question..."
        onChange={(e) =>
          setQuestion(e.target.value)
        }
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleSend();
          }
        }}
      />

      <button
        disabled={loading}
        onClick={handleSend}
      >
        Send
      </button>

      {loading && (
        <span className="thinking">
          Thinking...
        </span>
      )}

    </div>
  );
}

export default MessageInput;