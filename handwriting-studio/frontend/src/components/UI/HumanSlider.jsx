import { motion } from "framer-motion";

const descriptions = [
  [0, 0.2, "Very rushed"],
  [0.2, 0.4, "Bit hurried"],
  [0.4, 0.6, "Normal pace"],
  [0.6, 0.8, "Taking care"],
  [0.8, 1.01, "Very deliberate"]
];

export default function HumanSlider({ label, value, onChange, leftEmoji, rightEmoji, descriptionsOverride }) {
  const text = (descriptionsOverride || descriptions).find(([min, max]) => value >= min && value < max)?.[2] || "Normal pace";
  return (
    <div className="rounded-xl border border-border-warm bg-white p-4 shadow-warm">
      <div className="mb-3 flex items-center justify-between gap-4">
        <label className="font-serif text-lg font-semibold text-ui-warm">{label}</label>
        <span className="rounded-full bg-bg-warm px-3 py-1 text-xs font-semibold text-ui-warm">{text}</span>
      </div>
      <div className="flex items-center gap-3">
        <span aria-hidden className="text-xl">{leftEmoji}</span>
        <div className="relative h-7 flex-1">
          <div className="absolute left-0 right-0 top-1/2 h-2 -translate-y-1/2 rounded-full bg-[#e9dfd2]" />
          <motion.div className="absolute left-0 top-1/2 h-2 -translate-y-1/2 rounded-full bg-ui-accent" style={{ width: `${value * 100}%` }} />
          <input
            aria-label={label}
            className="absolute inset-0 h-7 w-full cursor-pointer opacity-0"
            min="0"
            max="1"
            step="0.01"
            type="range"
            value={value}
            onChange={(event) => onChange(Number(event.target.value))}
          />
          <motion.div className="absolute top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-2 border-white bg-ui-accent shadow" animate={{ left: `calc(${value * 100}% - 10px)` }} />
        </div>
        <span aria-hidden className="text-xl">{rightEmoji}</span>
      </div>
    </div>
  );
}

