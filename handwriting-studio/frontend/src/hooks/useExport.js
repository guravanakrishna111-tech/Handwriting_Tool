import { pdfExportUrl } from "../api/handwritingAPI";
import { useStudioStore } from "../store/studioStore";

export function useExport() {
  const sessionId = useStudioStore((s) => s.sessionId);
  function exportPdf() {
    if (sessionId) window.open(pdfExportUrl(sessionId), "_blank", "noopener,noreferrer");
  }
  return { exportPdf, canExport: Boolean(sessionId) };
}

