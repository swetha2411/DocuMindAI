import { useState } from "react";
import axios from "axios";

function UploadPanel({ onReady }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/upload`,
        formData
      );

      setMessage(
        `Ready! ${response.data.chunks} chunks stored.`
      );

      onReady();

    } catch (error) {
      console.error(error);
      setMessage("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-panel">

      <label className="upload-box">

        Click to upload PDF

        <input
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          hidden
        />

      </label>

      {loading && <p>Uploading PDF...</p>}

      {message && <p>{message}</p>}

    </div>
  );
}

export default UploadPanel;