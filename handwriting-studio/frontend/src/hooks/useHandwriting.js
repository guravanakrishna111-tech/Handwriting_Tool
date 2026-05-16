import { analyzeSample, generateHandwriting } from "../api/handwritingAPI";
import { useStudioStore } from "../store/studioStore";

export function useHandwriting() {
  const store = useStudioStore();

  async function analyze(file) {
    store.setError(null);
    store.setAnalyzing(true);
    try {
      const data = await analyzeSample(file);
      store.setSessionId(data.session_id);
      store.setStyleProfile(data.style_profile_summary);
      store.setPreviewChars(data.preview_chars || []);
    } catch (error) {
      store.setError(error.message);
    } finally {
      store.setAnalyzing(false);
    }
  }

  async function generate() {
    if (!store.sessionId) {
      store.setError("Upload a handwriting sample first.");
      return;
    }
    store.setError(null);
    store.setGenerating(true);
    try {
      const carefulness = Math.max(0, Math.min(1, (store.settings.carefulness + (1 - store.settings.exam_rush) + store.settings.letter_consistency) / 3));
      const data = await generateHandwriting({
        session_id: store.sessionId,
        text: store.inputText,
        settings: {
          carefulness,
          fatigue_rate: store.settings.fatigue_rate,
          ink_flow: store.settings.ink_flow,
          margin_discipline: store.settings.margin_discipline,
          paper_preset: store.settings.paper_preset,
          ink_preset: store.settings.ink_preset
        }
      });
      store.setPages(data.pages || []);
      store.setCurrentPage(0);
    } catch (error) {
      store.setError(error.message);
    } finally {
      store.setGenerating(false);
    }
  }

  return { analyze, generate };
}

