import { motion } from "framer-motion";
import HumanSlider from "../UI/HumanSlider";
import InkPreset from "../UI/InkPreset";
import PaperPreset from "../UI/PaperPreset";
import { useStudioStore } from "../../store/studioStore";

const rushDescriptions = [
  [0, 0.2, "Unhurried"],
  [0.2, 0.4, "Steady"],
  [0.4, 0.6, "Exam pace"],
  [0.6, 0.8, "Pushing time"],
  [0.8, 1.01, "Last minute"]
];

export default function ControlPanel() {
  const settings = useStudioStore((s) => s.settings);
  const updateSettings = useStudioStore((s) => s.updateSettings);
  const slider = (key) => (value) => updateSettings({ [key]: value });
  return (
    <motion.div layout className="space-y-4">
      <HumanSlider label="Writing Carefulness" value={settings.carefulness} onChange={slider("carefulness")} leftEmoji="🏃" rightEmoji="✍️" />
      <HumanSlider label="Exam Rush" value={settings.exam_rush} onChange={slider("exam_rush")} leftEmoji="😌" rightEmoji="⏱️" descriptionsOverride={rushDescriptions} />
      <HumanSlider label="Writer Fatigue" value={settings.fatigue_rate} onChange={slider("fatigue_rate")} leftEmoji="Fresh" rightEmoji="Tired" descriptionsOverride={rushDescriptions} />
      <HumanSlider label="Ink Flow" value={settings.ink_flow} onChange={slider("ink_flow")} leftEmoji="Dry" rightEmoji="Wet" />
      <HumanSlider label="Letter Consistency" value={settings.letter_consistency} onChange={slider("letter_consistency")} leftEmoji="Loose" rightEmoji="Even" />
      <HumanSlider label="Margin Discipline" value={settings.margin_discipline} onChange={slider("margin_discipline")} leftEmoji="Wanders" rightEmoji="Straight" />
      <div className="rounded-xl border border-border-warm bg-white p-4 shadow-warm">
        <div className="mb-3 font-serif text-lg font-semibold text-ui-warm">Paper</div>
        <PaperPreset value={settings.paper_preset} onChange={(paper_preset) => updateSettings({ paper_preset })} />
      </div>
      <div className="rounded-xl border border-border-warm bg-white p-4 shadow-warm">
        <div className="mb-3 font-serif text-lg font-semibold text-ui-warm">Ink</div>
        <InkPreset value={settings.ink_preset} onChange={(ink_preset) => updateSettings({ ink_preset })} />
      </div>
    </motion.div>
  );
}

