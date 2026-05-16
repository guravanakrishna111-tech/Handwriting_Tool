import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { useHandwriting } from "../../hooks/useHandwriting";
import { useStudioStore } from "../../store/studioStore";

export default function SampleUploader() {
  const inputRef = useRef(null);
  const [thumb, setThumb] = useState(null);
  const { analyze } = useHandwriting();
  const { isAnalyzing, styleProfile, previewChars } = useStudioStore();

  async function handleFile(file) {
    if (!file) return;
    if (file.type.startsWith("image/")) setThumb(URL.createObjectURL(file));
    await analyze(file);
  }

  return (
    <motion.div
      className="rounded-xl border border-border-warm bg-white p-4 shadow-warm"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        handleFile(event.dataTransfer.files?.[0]);
      }}
    >
      <motion.button
        type="button"
        whileHover={{ borderStyle: "solid", scale: 1.01 }}
        onClick={() => inputRef.current?.click()}
        className="flex w-full items-center gap-4 rounded-xl border-2 border-dashed border-border-warm bg-bg-warm/60 p-4 text-left transition hover:border-ui-accent"
      >
        <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-border-warm bg-paper-cream">
          {thumb ? <img src={thumb} alt="Sample thumbnail" className="h-full w-full object-cover" /> : <span className="text-2xl">✍️</span>}
        </div>
        <div>
          <div className="font-serif text-xl font-semibold text-ui-warm">Handwriting sample</div>
          <div className="mt-1 text-sm text-stone-600">{isAnalyzing ? "Analyzing style..." : "Drop a JPG, PNG, or PDF sample"}</div>
        </div>
      </motion.button>
      <input ref={inputRef} hidden type="file" accept="image/png,image/jpeg,application/pdf" onChange={(event) => handleFile(event.target.files?.[0])} />
      {styleProfile && (
        <div className="mt-4 flex flex-wrap gap-2">
          <Chip>Slant: {styleProfile.slant_label}</Chip>
          <Chip>Pressure: {styleProfile.pressure}</Chip>
          <Chip>Style: {styleProfile.style}</Chip>
        </div>
      )}
      {previewChars?.length > 0 && (
        <div className="mt-4 flex max-h-20 flex-wrap gap-2 overflow-hidden">
          {previewChars.slice(0, 12).map((item, index) => (
            <div key={`${item.char}-${index}`} className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-warm bg-paper-cream">
              <img src={item.image} alt={item.char} className="h-8 w-8 object-contain mix-blend-multiply" />
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function Chip({ children }) {
  return <span className="rounded-full border border-border-warm bg-paper-cream px-3 py-1 text-xs font-semibold text-ui-warm">{children}</span>;
}

