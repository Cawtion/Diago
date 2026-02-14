import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className, ...props }, ref) => (
    <label
      className={cn(
        "inline-flex items-center gap-2 text-sm text-subtext cursor-pointer select-none",
        "hover:text-text transition-colors",
        className
      )}
    >
      <input
        ref={ref}
        type="checkbox"
        className="w-4 h-4 rounded border-surface1 bg-surface0 text-primary focus:ring-primary/40 accent-primary cursor-pointer"
        {...props}
      />
      {label}
    </label>
  )
);

Checkbox.displayName = "Checkbox";
