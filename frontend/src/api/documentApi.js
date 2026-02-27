import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000",
});

// Upload Document
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await API.post("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

// Get User Documents
export const getDocuments = async () => {
  const response = await API.get("/documents");
  return response.data;
};