import NotebookCanvas from "../Canvas/NotebookCanvas";
import Toolbar from "./Toolbar";
import { useStudioStore } from "../../store/studioStore";

export default function PreviewPanel() {
  const error = useStudioStore((s) => s.error);
  return (
    <div className="flex h-full flex-col gap-4">
      <Toolbar />
      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">{error}</div>}
      <NotebookCanvas />
    </div>
  );
}

