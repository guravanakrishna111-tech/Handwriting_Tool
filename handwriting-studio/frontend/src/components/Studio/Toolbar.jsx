import { useExport } from "../../hooks/useExport";
import { useStudioStore } from "../../store/studioStore";

export default function Toolbar() {
  const { exportPdf, canExport } = useExport();
  const zoom = useStudioStore((s) => s.zoom);
  const setZoom = useStudioStore((s) => s.setZoom);
  return (
    <div className="flex items-center justify-between rounded-xl border border-border-warm bg-white px-4 py-3 shadow-warm">
      <div>
        <div className="font-serif text-xl font-semibold text-ui-warm">Preview</div>
        <div className="text-xs text-stone-500">A4 at 150 DPI</div>
      </div>
      <div className="flex items-center gap-2">
        <button type="button" className="h-9 w-9 rounded-lg border border-border-warm font-semibold text-ui-warm" onClick={() => setZoom(zoom - 0.1)} title="Zoom out">-</button>
        <span className="w-14 text-center font-mono text-xs text-stone-600">{Math.round(zoom * 100)}%</span>
        <button type="button" className="h-9 w-9 rounded-lg border border-border-warm font-semibold text-ui-warm" onClick={() => setZoom(zoom + 0.1)} title="Zoom in">+</button>
        <button type="button" disabled={!canExport} onClick={exportPdf} className="ml-2 rounded-lg bg-ui-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-45">
          PDF
        </button>
      </div>
    </div>
  );
}

