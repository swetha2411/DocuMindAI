import { useEffect, useRef } from "react";
import SourceSection from "./SourceSection";

function ChatWindow({ messages }) {

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth"
    });
  }, [messages]);

  return (
    <div className="chat-window">

      {messages.map((msg, index) => (

        <div
          key={index}
          className={
            msg.sender === "user"
              ? "user-message"
              : "bot-message"
          }
        >

          <p>{msg.text}</p>

          {msg.sender === "bot" &&
            msg.sources && (
              <SourceSection
                sources={msg.sources}
              />
          )}

        </div>

      ))}

      <div ref={bottomRef}></div>

    </div>
  );
}

export default ChatWindow;