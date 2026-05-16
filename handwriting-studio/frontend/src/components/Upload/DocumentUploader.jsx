import { useRef } from "react";
import { useStudioStore } from "../../store/studioStore";

export default function DocumentUploader() {
  const ref = useRef(null);
  const setInputText = useStudioStore((s) => s.setInputText);
  async function loadFile(file) {
    if (!file) return;
    const text = await file.text();
    setInputText(text);
  }
  return (
    <div className="rounded-xl border border-border-warm bg-white p-3 shadow-warm">
      <button type="button" onClick={() => ref.current?.click()} className="w-full rounded-lg border border-border-warm px-3 py-2 text-sm font-semibold text-ui-warm hover:border-ui-accent">
        Import text file
      </button>
      <input ref={ref} hidden type="file" accept=".txt,.md,text/plain" onChange={(event) => loadFile(event.target.files?.[0])} />
    </div>
  );
}

