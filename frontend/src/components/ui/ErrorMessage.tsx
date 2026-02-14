import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  className?: string;
  compact?: boolean;
}

export function ErrorMessage({
  message,
  onRetry,
  className,
  compact,
}: ErrorMessageProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg border border-red/30 bg-red/5 px-3 py-2 text-sm text-red",
        compact && "py-1.5 text-xs",
        className
      )}
      role="alert"
    >
      <AlertTriangle size={compact ? 14 : 16} className="shrink-0" />
      <span className="flex-1">{message}</span>
      {onRetry && (
        <Button variant="ghost" size="sm" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry
        </Button>
      )}
    </div>
  );
}
