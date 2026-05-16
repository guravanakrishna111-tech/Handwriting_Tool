import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
});

function unwrapError(error) {
  const data = error.response?.data;
  if (data?.detail) return `${data.error || "Request failed"}: ${data.detail}`;
  if (data?.error) return `${data.error}: ${data.detail || ""}`;
  return error.message || "Request failed";
}

export async function analyzeSample(file) {
  const form = new FormData();
  form.append("file", file);
  try {
    const { data } = await client.post("/api/analyze", form, { headers: { "Content-Type": "multipart/form-data" } });
    return data;
  } catch (error) {
    throw new Error(unwrapError(error));
  }
}

export async function generateHandwriting(payload) {
  try {
    const { data } = await client.post("/api/generate", payload);
    return data;
  } catch (error) {
    throw new Error(unwrapError(error));
  }
}

export async function regeneratePage(payload) {
  try {
    const { data } = await client.post("/api/regenerate", payload);
    return data;
  } catch (error) {
    throw new Error(unwrapError(error));
  }
}

export function pdfExportUrl(sessionId) {
  return `${API_BASE_URL}/api/export/pdf/${sessionId}`;
}
