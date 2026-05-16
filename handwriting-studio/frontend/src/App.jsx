import { motion } from "framer-motion";
import { Route, Routes } from "react-router-dom";
import ControlPanel from "./components/Studio/ControlPanel";
import InputPanel from "./components/Studio/InputPanel";
import PreviewPanel from "./components/Studio/PreviewPanel";

function Studio() {
  return (
    <main className="min-h-screen bg-bg-warm p-5">
      <div className="mx-auto grid max-w-[1720px] grid-cols-[minmax(460px,40%)_minmax(700px,60%)] gap-5">
        <motion.section initial={{ x: -40, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ duration: 0.5 }} className="h-[calc(100vh-40px)] overflow-y-auto pr-1">
          <div className="mb-5">
            <h1 className="font-serif text-4xl font-bold text-ui-warm">Handwriting Studio</h1>
            <p className="mt-1 text-sm text-stone-600">Typed text rendered through your extracted handwriting sample.</p>
          </div>
          <div className="space-y-5">
            <InputPanel />
            <ControlPanel />
          </div>
        </motion.section>
        <section className="h-[calc(100vh-40px)] overflow-hidden">
          <PreviewPanel />
        </section>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="*" element={<Studio />} />
    </Routes>
  );
}

