import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format seconds as mm:ss */
export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Format a timestamp string to a readable date */
export function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Get color for OBD code prefix */
export function codeColor(code: string): string {
  const prefix = code.charAt(0).toUpperCase();
  switch (prefix) {
    case "P":
      return "var(--color-yellow)";
    case "B":
      return "var(--color-blue)";
    case "C":
      return "var(--color-green)";
    case "U":
      return "var(--color-purple)";
    default:
      return "var(--color-text)";
  }
}

/** Get confidence color */
export function confidenceColor(confidence: string): string {
  switch (confidence.toLowerCase()) {
    case "high":
      return "var(--color-green)";
    case "medium":
      return "var(--color-yellow)";
    case "low":
      return "var(--color-red)";
    default:
      return "var(--color-subtext)";
  }
}

/** Generate a unique id */
export function uid(): string {
  return Math.random().toString(36).slice(2, 11);
}
