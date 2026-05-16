"use client";

import { DragEvent, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Clipboard, Download, FileSearch, FileText, PenLine, RefreshCw, UploadCloud } from "lucide-react";
import {
  analyzeReference,
  apiUrl,
  extractSourceText,
  generateHandwriting,
  GenerateResponse,
  ReferenceAnalyzeResponse,
  StudioSettings
} from "@/lib/api";
import { StudioPreview } from "@/components/studio-preview";

const defaultSettings: StudioSettings = {
  writing_carefulness: 0.62,
  exam_rush: 0.38,
  writer_fatigue: 0.35,
  ink_flow: 0.58,
  letter_consistency: 0.48,
  margin_discipline: 0.62,
  mood_variation: 0.25,
  handedness: "right",
  paper_preset: "ruled",
  ink_preset: "blue_gel",
  output_format: "pdf"
};

const controls = [
  ["writing_carefulness", "Writing Carefulness"],
  ["exam_rush", "Exam Rush"],
  ["writer_fatigue", "Writer Fatigue"],
  ["ink_flow", "Ink Flow"],
  ["letter_consistency", "Letter Consistency"],
  ["margin_discipline", "Margin Discipline"]
] as const;

export default function Page() {
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [referenceAnalysis, setReferenceAnalysis] = useState<ReferenceAnalyzeResponse | null>(null);
  const [text, setText] = useState("");
  const [settings, setSettings] = useState<StudioSettings>(defaultSettings);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [zoom, setZoom] = useState(0.72);
  const referenceLabel = useMemo(() => referenceFiles.length ? `${referenceFiles.length} reference page${referenceFiles.length > 1 ? "s" : ""}` : "Upload handwriting reference", [referenceFiles]);

  async function onReference(files: File[]) {
    if (!files.length) return;
    setReferenceFiles(files);
    setBusy("Analyzing handwriting");
    try {
      setReferenceAnalysis(await analyzeReference(files));
    } finally {
      setBusy(null);
    }
  }

  async function onSource(file: File) {
    setSourceFile(file);
    setBusy("Extracting source text");
    try {
      const extracted = await extractSourceText(file);
      setText(extracted.text);
    } finally {
      setBusy(null);
    }
  }

  async function submit() {
    if (!referenceFiles.length || !text.trim()) return;
    setBusy("Generating handwriting");
    try {
      setResult(await generateHandwriting(text, referenceFiles, settings));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="flex h-screen min-h-[820px] overflow-hidden font-ui">
      <section className="flex w-[560px] flex-col bg-[#fbf4e5]/95 shadow-[12px_0_40px_rgba(68,45,20,0.08)]">
        <div className="border-b border-black/10 px-6 py-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-clay">Handwriting Studio</p>
          <h1 className="mt-1 font-studio text-4xl leading-none">Intelligent writing reproduction</h1>
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-6 py-5">
          <UploadCard
            title={referenceLabel}
            subtitle="JPG, PNG, or PDF. Multiple pages supported."
            accept="image/*,.pdf"
            multiple
            icon="reference"
            onFiles={onReference}
          />

          {referenceAnalysis && (
            <div className="mt-3 rounded border border-black/10 bg-white/55 p-3">
              <div className="flex justify-between text-xs text-black/60">
                <span>{referenceAnalysis.page_count} page style profile</span>
                <span>quality {Math.round(referenceAnalysis.quality_score * 100)}%</span>
              </div>
              <div className="mt-3 flex gap-2 overflow-x-auto">
                {referenceAnalysis.preview_data_urls.map((url, index) => (
                  <img key={index} src={url} alt={`Reference page ${index + 1}`} className="h-28 rounded border border-black/10 bg-white object-cover" />
                ))}
              </div>
            </div>
          )}

          <div className="mt-4">
            <UploadCard
              title={sourceFile?.name ?? "Upload source document"}
              subtitle="PDF, DOCX, TXT, or image document. Text is extracted for editing."
              accept=".pdf,.docx,.txt,image/*"
              icon="source"
              onFiles={(files) => files[0] && onSource(files[0])}
            />
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            <Select label="Paper" value={settings.paper_preset} onChange={(paper_preset) => setSettings({ ...settings, paper_preset: paper_preset as StudioSettings["paper_preset"] })} options={[
              ["ruled", "Ruled notebook"],
              ["plain_a4", "Plain A4"],
              ["exam_sheet", "Exam sheet"],
              ["vintage", "Vintage paper"]
            ]} />
            <Select label="Ink" value={settings.ink_preset} onChange={(ink_preset) => setSettings({ ...settings, ink_preset: ink_preset as StudioSettings["ink_preset"] })} options={[
              ["blue_gel", "Blue gel"],
              ["black_ball", "Black ball"],
              ["fountain", "Fountain"],
              ["pencil", "Pencil"]
            ]} />
          </div>

          <div className="mt-5 flex items-center justify-between">
            <p className="text-sm font-semibold">Extracted text preview</p>
            <button className="flex items-center gap-2 rounded border border-black/10 bg-white/70 px-3 py-2 text-xs" onClick={() => navigator.clipboard.writeText(text)} disabled={!text}>
              <Clipboard size={14} />
              Copy Extracted Text
            </button>
          </div>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            className="mt-2 h-56 w-full resize-none rounded border border-black/10 bg-white/75 p-4 font-ui text-sm leading-6 outline-none focus:border-clay"
            placeholder="Upload a source document or paste text here, then edit before generating."
          />

          <div className="mt-5 space-y-4">
            {controls.map(([key, label]) => (
              <label key={key} className="block">
                <div className="mb-1 flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="text-black/50">{Math.round(settings[key] * 100)}</span>
                </div>
                <input className="range w-full" type="range" min={0} max={1} step={0.01} value={settings[key]} onChange={(event) => setSettings({ ...settings, [key]: Number(event.target.value) })} />
              </label>
            ))}
          </div>
        </div>

        <div className="border-t border-black/10 p-5">
          <div className="grid grid-cols-2 gap-2">
            <button className="flex h-11 items-center justify-center gap-2 rounded bg-ink px-3 text-sm text-white disabled:opacity-45" onClick={submit} disabled={!!busy || !referenceFiles.length || !text.trim()}>
              {busy ? <RefreshCw className="animate-spin" size={16} /> : <PenLine size={16} />}
              {busy ?? "Generate Handwriting"}
            </button>
            <a className="flex h-11 items-center justify-center gap-2 rounded border border-black/10 bg-white/65 px-3 text-sm aria-disabled:pointer-events-none aria-disabled:opacity-45" href={result ? apiUrl(result.download_url) : "#"} aria-disabled={!result}>
              <Download size={16} />
              Export PDF
            </a>
          </div>
          <motion.p animate={{ opacity: result?.text_preserved ? 1 : 0.55 }} className="mt-3 flex items-center gap-2 text-xs text-black/55">
            <FileText size={14} />
            Exact source text is preserved; extraction stays editable before generation.
          </motion.p>
        </div>
      </section>

      <StudioPreview result={result} zoom={zoom} onZoom={setZoom} />
    </main>
  );
}

function UploadCard({
  title,
  subtitle,
  accept,
  multiple,
  icon,
  onFiles
}: {
  title: string;
  subtitle: string;
  accept: string;
  multiple?: boolean;
  icon: "reference" | "source";
  onFiles: (files: File[]) => void;
}) {
  const [dragging, setDragging] = useState(false);
  function drop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    onFiles(Array.from(event.dataTransfer.files));
  }
  const Icon = icon === "reference" ? UploadCloud : FileSearch;
  return (
    <motion.label
      animate={{ scale: dragging ? 1.01 : 1, borderColor: dragging ? "rgba(169,71,52,0.65)" : "rgba(0,0,0,0.2)" }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={drop}
      className="grid cursor-pointer place-items-center rounded border border-dashed bg-white/55 p-5 text-center shadow-sm"
    >
      <Icon className="mb-2 text-moss" />
      <span className="font-ui text-sm font-semibold">{title}</span>
      <span className="mt-1 text-xs text-black/55">{subtitle}</span>
      <input className="sr-only" type="file" accept={accept} multiple={multiple} onChange={(event) => onFiles(Array.from(event.target.files ?? []))} />
    </motion.label>
  );
}

function Select({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: [string, string][];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-black/55">{label}</span>
      <select className="h-10 w-full rounded border border-black/10 bg-white/70 px-2 text-sm outline-none" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([key, name]) => (
          <option key={key} value={key}>{name}</option>
        ))}
      </select>
    </label>
  );
}
