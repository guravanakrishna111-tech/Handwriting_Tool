import { useCallback } from "react";
import { useStudioStore } from "../store/studioStore";

export function useCanvas() {
  const zoom = useStudioStore((s) => s.zoom);
  const setZoom = useStudioStore((s) => s.setZoom);
  const onWheel = useCallback((event) => {
    event.evt.preventDefault();
    const direction = event.evt.deltaY > 0 ? -0.08 : 0.08;
    setZoom(zoom + direction);
  }, [setZoom, zoom]);
  return { zoom, setZoom, onWheel };
}

