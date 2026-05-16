import { useEffect, useState } from "react";
import { Image as KonvaImage, Rect, Group } from "react-konva";

export default function PageRenderer({ src, x, y, scale = 1 }) {
  const [image, setImage] = useState(null);
  useEffect(() => {
    if (!src) return;
    const img = new window.Image();
    img.onload = () => setImage(img);
    img.src = src;
  }, [src]);
  return (
    <Group x={x} y={y} scaleX={scale} scaleY={scale}>
      <Rect x={8} y={14} width={1240} height={1754} fill="rgba(78,64,46,0.22)" cornerRadius={3} />
      <Rect width={1240} height={1754} fill="#fffdf8" cornerRadius={2} shadowColor="rgba(78,64,46,0.22)" shadowBlur={20} shadowOffsetY={8} />
      {image && <KonvaImage image={image} width={1240} height={1754} />}
    </Group>
  );
}

