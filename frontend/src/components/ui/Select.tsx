import { type SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, className, ...props }, ref) => (
    <label className="flex flex-col gap-1 text-xs text-subtext">
      {label && <span>{label}</span>}
      <select
        ref={ref}
        className={cn(
          "bg-surface0 text-text border border-surface1 rounded-md px-3 py-1.5 text-sm",
          "focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary",
          "transition-colors cursor-pointer",
          className
        )}
        {...props}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
);

Select.displayName = "Select";
