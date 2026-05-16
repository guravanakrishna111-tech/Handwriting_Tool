import { motion } from "framer-motion";
import { Layer, Rect, Stage, Text } from "react-konva";
import { useCanvas } from "../../hooks/useCanvas";
import { useStudioStore } from "../../store/studioStore";
import PageRenderer from "./PageRenderer";

export default function NotebookCanvas() {
  const pages = useStudioStore((s) => s.pages);
  const isGenerating = useStudioStore((s) => s.isGenerating);
  const { zoom, onWheel } = useCanvas();
  const stageWidth = Math.max(720, window.innerWidth * 0.56);
  const stageHeight = Math.max(760, window.innerHeight - 120);
  const previewScale = 0.42 * zoom;
  const x = Math.max(30, (stageWidth - 1240 * previewScale) / 2);

  if (!pages.length) {
    return (
      <div className="relative flex min-h-[760px] items-center justify-center overflow-hidden rounded-xl border border-border-warm bg-[#ece3d7] shadow-warm">
        <div className="relative h-[540px] w-[382px] rounded-sm bg-paper-cream shadow-page page-curl">
          <div className="absolute left-7 top-10 bottom-10 w-px bg-red-200" />
          {Array.from({ length: 15 }).map((_, i) => <div key={i} className="absolute left-0 right-0 h-px bg-blue-100" style={{ top: 74 + i * 28 }} />)}
          {isGenerating && <div className="writing-scan absolute left-0 right-0 top-0 h-16 bg-gradient-to-b from-transparent via-ui-accent/20 to-transparent" />}
          <div className="absolute inset-x-10 top-44 text-center font-serif text-2xl font-semibold text-ui-warm">{isGenerating ? "Writing..." : "Your generated pages appear here"}</div>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.4 }} className="relative overflow-auto rounded-xl border border-border-warm bg-[#ece3d7] shadow-warm">
      <Stage width={stageWidth} height={stageHeight} draggable={zoom > 1} onWheel={onWheel}>
        <Layer>
          <Rect width={stageWidth} height={stageHeight + pages.length * 40} fill="#ece3d7" />
          {pages.map((page, index) => (
            <PageRenderer key={`${index}-${page.slice(0, 40)}`} src={page} x={x} y={34 + index * (1754 * previewScale + 20)} scale={previewScale} />
          ))}
          <Text x={20} y={20} text={`${pages.length} page${pages.length === 1 ? "" : "s"}`} fontFamily="Inter" fontSize={13} fill="#8B7355" />
        </Layer>
      </Stage>
      <div className="pointer-events-none absolute bottom-0 right-0 h-24 w-24 bg-gradient-to-br from-transparent to-black/10" />
    </motion.div>
  );
}

