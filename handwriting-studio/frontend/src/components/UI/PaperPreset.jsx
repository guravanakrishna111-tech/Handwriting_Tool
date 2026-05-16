const presets = [
  ["ruled_notebook", "Notebook", "lined"],
  ["plain_a4", "Plain", "clean"],
  ["exam_sheet", "Exam", "boxed"],
  ["vintage", "Vintage", "aged"]
];

export default function PaperPreset({ value, onChange }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {presets.map(([id, label, hint]) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={`rounded-xl border p-3 text-left transition ${value === id ? "border-ui-accent bg-[#fff8ef]" : "border-border-warm bg-white hover:border-ui-warm"}`}
          title={hint}
        >
          <div className="mb-2 h-12 rounded-lg border border-border-warm bg-paper-cream px-2 py-2">
            {id !== "plain_a4" && <div className="space-y-1.5">{[0, 1, 2].map((n) => <div key={n} className="h-px bg-blue-200" />)}</div>}
            {id === "exam_sheet" && <div className="mt-1 h-3 rounded border border-blue-200" />}
            {id === "vintage" && <div className="h-full rounded bg-paper-aged opacity-80" />}
          </div>
          <span className="text-sm font-semibold text-ui-warm">{label}</span>
        </button>
      ))}
    </div>
  );
}

