import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface ChipProps {
  label: string;
  color?: string;
  onRemove?: () => void;
  onClick?: () => void;
  className?: string;
}

export function Chip({ label, color, onRemove, onClick, className }: ChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium",
        "border border-surface1 bg-surface0 text-text transition-colors",
        onClick && "cursor-pointer hover:bg-surface1",
        className
      )}
      style={color ? { borderColor: color, color } : undefined}
      onClick={onClick}
    >
      {label}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 rounded-full p-0.5 hover:bg-surface1 transition-colors cursor-pointer"
        >
          <X size={12} />
        </button>
      )}
    </span>
  );
}
