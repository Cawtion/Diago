import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useToastStore, type ToastType } from "@/stores/toastStore";
import { cn } from "@/lib/utils";

const icons: Record<ToastType, typeof Info> = {
  error: AlertCircle,
  success: CheckCircle2,
  info: Info,
};

const styles: Record<ToastType, string> = {
  error: "border-red/50 bg-surface0 text-red",
  success: "border-green/50 bg-surface0 text-green",
  info: "border-primary/50 bg-surface0 text-primary",
};

export function Toast() {
  const { message, type, hide } = useToastStore();

  if (!message) return null;

  const Icon = icons[type];

  return (
    <div
      role="alert"
      className={cn(
        "fixed bottom-6 left-1/2 -translate-x-1/2 z-[100]",
        "flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg max-w-[min(90vw,28rem)]",
        styles[type]
      )}
    >
      <Icon size={20} className="shrink-0" />
      <p className="text-sm text-text flex-1">{message}</p>
      <button
        type="button"
        onClick={hide}
        className="p-1 rounded hover:bg-surface1 text-overlay0 hover:text-text transition-colors"
        aria-label="Dismiss"
      >
        <X size={16} />
      </button>
    </div>
  );
}
