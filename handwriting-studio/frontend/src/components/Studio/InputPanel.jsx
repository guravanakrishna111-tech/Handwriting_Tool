import DocumentUploader from "../Upload/DocumentUploader";
import SampleUploader from "../Upload/SampleUploader";
import { useHandwriting } from "../../hooks/useHandwriting";
import { useStudioStore } from "../../store/studioStore";

export default function InputPanel() {
  const inputText = useStudioStore((s) => s.inputText);
  const setInputText = useStudioStore((s) => s.setInputText);
  const isGenerating = useStudioStore((s) => s.isGenerating);
  const { generate } = useHandwriting();
  return (
    <div className="space-y-4">
      <SampleUploader />
      <DocumentUploader />
      <div className="rounded-xl border border-border-warm bg-white p-4 shadow-warm">
        <div className="mb-3 flex items-center justify-between">
          <label className="font-serif text-xl font-semibold text-ui-warm">Assignment text</label>
          <span className="font-mono text-xs text-stone-500">{inputText.length} chars</span>
        </div>
        <textarea
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          className="h-56 w-full resize-none rounded-lg border border-border-warm bg-[#fffdf9] p-3 font-mono text-sm leading-6 outline-none focus:border-ui-accent"
          spellCheck="false"
        />
        <button type="button" onClick={generate} disabled={isGenerating} className="mt-3 w-full rounded-lg bg-ui-warm px-4 py-3 font-semibold text-white shadow-warm transition hover:bg-[#765f45] disabled:cursor-wait disabled:opacity-60">
          {isGenerating ? "Writing pages..." : "Generate handwriting"}
        </button>
      </div>
    </div>
  );
}

