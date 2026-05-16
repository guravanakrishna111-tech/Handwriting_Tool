"use client";

import { Image as ImageIcon, ZoomIn, ZoomOut } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Image as KonvaImage, Layer, Rect, Stage } from "react-konva/lib/ReactKonvaCore";
import "konva/lib/shapes/Image";
import "konva/lib/shapes/Rect";
import { apiUrl, GenerateResponse } from "@/lib/api";

type Props = {
  result: GenerateResponse | null;
  zoom: number;
  onZoom: (zoom: number) => void;
};

export function StudioPreview({ result, zoom, onZoom }: Props) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const previewUrl = result ? apiUrl(result.preview_url) : null;

  useEffect(() => {
    if (!previewUrl) {
      setImage(null);
      return;
    }
    const nextImage = new window.Image();
    nextImage.crossOrigin = "anonymous";
    nextImage.onload = () => setImage(nextImage);
    nextImage.src = previewUrl;
  }, [previewUrl]);

  return (
    <section className="flex min-h-0 flex-1 flex-col border-l border-black/10 bg-[#eee1c7]/70">
      <div className="flex items-center justify-between border-b border-black/10 px-5 py-3">
        <div>
          <p className="font-ui text-[11px] uppercase tracking-[0.18em] text-clay">Live Preview</p>
          <h2 className="font-studio text-2xl">Notebook render</h2>
        </div>
        <div className="flex items-center gap-2">
          <button className="grid h-9 w-9 place-items-center rounded border border-black/10 bg-white/70" onClick={() => onZoom(Math.max(0.45, zoom - 0.1))} title="Zoom out">
            <ZoomOut size={17} />
          </button>
          <span className="w-14 text-center font-ui text-sm">{Math.round(zoom * 100)}%</span>
          <button className="grid h-9 w-9 place-items-center rounded border border-black/10 bg-white/70" onClick={() => onZoom(Math.min(1.35, zoom + 0.1))} title="Zoom in">
            <ZoomIn size={17} />
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-8">
        <motion.div
          animate={{ scale: zoom }}
          transition={{ type: "spring", stiffness: 150, damping: 22 }}
          className="mx-auto origin-top"
          style={{ width: 720 }}
        >
          {result && image ? (
            <div className="overflow-hidden rounded-sm bg-paper shadow-paper">
              <Stage width={720} height={1018}>
                <Layer>
                  <Rect x={0} y={0} width={720} height={1018} fill="#f7f0df" />
                  <KonvaImage image={image} x={0} y={0} width={720} height={1018} />
                </Layer>
              </Stage>
            </div>
          ) : (
            <div className="paper-grain grid aspect-[0.707/1] w-full place-items-center rounded-sm border border-black/10 shadow-paper">
              <div className="grid place-items-center gap-3 text-center text-black/45">
                <ImageIcon size={36} />
                <p className="max-w-xs font-ui text-sm">Preview pages appear here after a sample and exact text are submitted.</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
