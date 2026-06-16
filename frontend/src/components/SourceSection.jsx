import { useState } from "react";

function SourceSection({ sources }) {

  const [open, setOpen] = useState(false);

  return (
    <div className="sources-section">

      <button
        className="source-toggle"
        onClick={() => setOpen(!open)}
      >
        {open ? "▼" : "▶"} Sources
      </button>

      {open && (
        <div className="source-list">

          {sources.map((source, index) => (

            <div
              key={index}
              className="source-card"
            >

              <strong>
                Page {source.page}
              </strong>

              <p>
                {source.text}
              </p>

            </div>

          ))}

        </div>
      )}
    </div>
  );
}

export default SourceSection;