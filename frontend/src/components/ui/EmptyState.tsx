import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  className?: string;
  iconClassName?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  className,
  iconClassName,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 text-center p-6",
        className
      )}
    >
      <Icon
        size={40}
        className={cn("text-surface2", iconClassName)}
        aria-hidden
      />
      <p className="text-subtext text-sm font-medium">{title}</p>
      {description && (
        <p className="text-overlay0 text-xs max-w-[240px]">{description}</p>
      )}
    </div>
  );
}
