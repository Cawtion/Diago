import { cn } from "@/lib/utils";

type DensityVariant = "relaxed" | "compact";

interface SectionCardProps {
  title?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  variant?: DensityVariant;
}

export function SectionCard({ title, children, className, variant = "relaxed" }: SectionCardProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-surface1/80 card-shadow",
        variant === "relaxed" && "bg-mantle/80 p-5",
        variant === "compact" && "bg-mantle/60 p-3",
        className
      )}
    >
      {title != null && (
        <h2 className="text-sm font-medium text-subtext mb-3 flex items-center gap-2 tracking-tight">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}
