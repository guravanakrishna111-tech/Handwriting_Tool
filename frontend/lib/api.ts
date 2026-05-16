export type StudioSettings = {
  writing_carefulness: number;
  exam_rush: number;
  writer_fatigue: number;
  ink_flow: number;
  letter_consistency: number;
  margin_discipline: number;
  mood_variation: number;
  handedness: "left" | "right";
  paper_preset: "ruled" | "plain_a4" | "exam_sheet" | "vintage";
  ink_preset: "blue_gel" | "black_ball" | "fountain" | "pencil";
  output_format: "pdf" | "png";
};

export type GenerateResponse = {
  session_id: string;
  page_count: number;
  preview_url: string;
  download_url: string;
  download_name: string;
  page_urls: string[];
  text_preserved: boolean;
};

export type ExtractTextResponse = {
  text: string;
  source_type: string;
  line_count: number;
  paragraph_count: number;
  confidence: number;
};

export type ReferenceAnalyzeResponse = {
  page_count: number;
  quality_score: number;
  ink_coverage: number;
  contrast_score: number;
  preview_data_urls: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_HANDWRITING_API ?? "http://127.0.0.1:8000";

export async function generateHandwriting(text: string, reference: File[], settings: StudioSettings) {
  const form = new FormData();
  form.set("text", text);
  reference.forEach((file) => form.append("reference", file));
  form.set("settings", JSON.stringify(settings));
  const response = await fetch(`${API_BASE}/api/generate-upload`, {
    method: "POST",
    body: form
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "Generation failed.");
  }
  return data as GenerateResponse;
}

export async function extractSourceText(source: File) {
  const form = new FormData();
  form.set("source", source);
  const response = await fetch(`${API_BASE}/api/source/extract`, {
    method: "POST",
    body: form
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "Text extraction failed.");
  }
  return data as ExtractTextResponse;
}

export async function analyzeReference(reference: File[]) {
  const form = new FormData();
  reference.forEach((file) => form.append("reference", file));
  const response = await fetch(`${API_BASE}/api/reference/analyze`, {
    method: "POST",
    body: form
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "Reference analysis failed.");
  }
  return data as ReferenceAnalyzeResponse;
}

export function apiUrl(path: string) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}
