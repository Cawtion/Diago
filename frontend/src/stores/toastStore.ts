import { create } from "zustand";

export type ToastType = "error" | "success" | "info";

export interface ToastState {
  message: string | null;
  type: ToastType;
  show: (message: string, type?: ToastType) => void;
  hide: () => void;
}

const AUTO_DISMISS_MS = 6000;

let dismissTimer: ReturnType<typeof setTimeout> | null = null;

export const useToastStore = create<ToastState>((set, get) => ({
  message: null,
  type: "info",

  show: (message, type = "info") => {
    if (dismissTimer) clearTimeout(dismissTimer);
    set({ message, type });
    dismissTimer = setTimeout(() => {
      get().hide();
      dismissTimer = null;
    }, AUTO_DISMISS_MS);
  },

  hide: () => {
    if (dismissTimer) {
      clearTimeout(dismissTimer);
      dismissTimer = null;
    }
    set({ message: null });
  },
}));
