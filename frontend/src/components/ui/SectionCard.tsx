import { cn } from "@/lib/utils";

interface SectionCardProps {
  title?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, children, className }: SectionCardProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-surface1 bg-surface0/50 p-4",
        className
      )}
    >
      {title != null && (
        <h2 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}
