import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number; // 0-100
  color?: string;
  label?: string;
  sublabel?: string;
  className?: string;
}

export function ProgressBar({
  value,
  color,
  label,
  sublabel,
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const useGradient = color === undefined;

  return (
    <div className={cn("flex items-center gap-3", className)}>
      {label && (
        <span className="text-sm text-subtext w-44 truncate shrink-0">
          {label}
        </span>
      )}
      <div className="flex-1 h-2.5 bg-surface0 rounded-full overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            useGradient && "progress-fill-gradient"
          )}
          style={{
            width: `${clamped}%`,
            ...(useGradient ? {} : { backgroundColor: color }),
          }}
        />
      </div>
      {sublabel && (
        <span className="text-xs text-subtext w-16 text-right shrink-0">
          {sublabel}
        </span>
      )}
    </div>
  );
}
