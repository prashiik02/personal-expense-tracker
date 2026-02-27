import { useState } from "react";
import axios from "axios";
import React from "react";
export default function UploadDocument() {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);

    await axios.post("http://localhost:5000/documents/upload", formData);
    alert("Uploaded successfully");
  };

  return (
    <div>
      <h2>Upload Document</h2>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}