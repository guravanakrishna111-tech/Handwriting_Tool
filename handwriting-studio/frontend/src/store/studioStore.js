import { create } from "zustand";

export const useStudioStore = create((set) => ({
  sessionId: null,
  sampleUploaded: false,
  styleProfile: null,
  previewChars: [],
  inputText: "Write your assignment text here. Every generated character will be pulled from the uploaded sample and nudged with small human variations.",
  settings: {
    carefulness: 0.58,
    exam_rush: 0.42,
    fatigue_rate: 0.24,
    ink_flow: 0.8,
    letter_consistency: 0.58,
    margin_discipline: 0.72,
    paper_preset: "ruled_notebook",
    ink_preset: "blue_gel"
  },
  pages: [],
  isAnalyzing: false,
  isGenerating: false,
  currentPage: 0,
  zoom: 1,
  error: null,
  setSessionId: (sessionId) => set({ sessionId, sampleUploaded: Boolean(sessionId) }),
  setStyleProfile: (styleProfile) => set({ styleProfile }),
  setPreviewChars: (previewChars) => set({ previewChars }),
  setInputText: (inputText) => set({ inputText }),
  updateSettings: (patch) => set((state) => ({ settings: { ...state.settings, ...patch } })),
  setPages: (pages) => set({ pages }),
  setZoom: (zoom) => set({ zoom: Math.max(0.5, Math.min(3, zoom)) }),
  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setGenerating: (isGenerating) => set({ isGenerating }),
  setCurrentPage: (currentPage) => set({ currentPage }),
  setError: (error) => set({ error })
}));

