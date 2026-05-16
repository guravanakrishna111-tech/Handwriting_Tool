const inks = [
  ["blue_gel", "Blue Gel", "#1a3a6e"],
  ["black_ball", "Black Ball", "#0a0a0a"],
  ["fountain", "Fountain", "#1c1c3a"],
  ["pencil", "Pencil", "#4a4a4a"]
];

export default function InkPreset({ value, onChange }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {inks.map(([id, label, color]) => (
        <button key={id} type="button" onClick={() => onChange(id)} className={`rounded-xl border bg-white p-3 text-left transition ${value === id ? "border-ui-accent" : "border-border-warm hover:border-ui-warm"}`}>
          <div className="mb-2 h-3 rounded-full" style={{ backgroundColor: color, opacity: id === "pencil" ? 0.72 : 1 }} />
          <span className="text-sm font-semibold text-ui-warm">{label}</span>
        </button>
      ))}
    </div>
  );
}

