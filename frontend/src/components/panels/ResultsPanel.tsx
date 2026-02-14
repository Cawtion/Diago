import {
  AlertTriangle,
  CheckCircle2,
  Download,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { EmptyState } from "@/components/ui/EmptyState";
import { useAppStore } from "@/stores/appStore";
import { confidenceColor } from "@/lib/utils";

export function ResultsPanel() {
  const diagnosis = useAppStore((s) => s.diagnosis);

  if (!diagnosis) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Run a diagnosis to see results here"
        description="Record or import audio, add symptoms or codes, then click Analyze."
        className="flex-1 p-8"
      />
    );
  }

  const confColor = confidenceColor(diagnosis.confidence);

  const ConfIcon =
    diagnosis.confidence === "high"
      ? CheckCircle2
      : diagnosis.confidence === "medium"
      ? AlertTriangle
      : XCircle;

  const handleExport = () => {
    const blob = new Blob([diagnosis.report_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diago_report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-5">
      {/* Confidence Banner */}
      <div
        className="rounded-lg p-4 border-l-4"
        style={{
          borderColor: confColor,
          backgroundColor: `color-mix(in srgb, ${confColor} 8%, var(--color-surface0))`,
        }}
      >
        <div className="flex items-start gap-3">
          <ConfIcon
            size={24}
            style={{ color: confColor }}
            className="shrink-0 mt-0.5"
          />
          <div>
            <h3 className="font-bold text-lg" style={{ color: confColor }}>
              {diagnosis.is_ambiguous
                ? "AMBIGUOUS RESULT"
                : diagnosis.top_class_display}
            </h3>
            <p className="text-sm text-subtext">
              Confidence: {diagnosis.confidence} | Fingerprint matches:{" "}
              {diagnosis.fingerprint_count}
            </p>
          </div>
        </div>
      </div>

      {/* Score Bars */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-text flex items-center gap-2">
          <span className="w-1 h-4 bg-primary rounded-full" />
          Mechanical Class Scores
        </h4>
        <div className="space-y-1.5">
          {diagnosis.class_scores.map((cs, index) => {
            const pct = cs.score * 100;
            const hasPenalty = cs.penalty > 0;
            const isTopBar = index === 0;
            return (
              <div key={cs.class_name} className="flex items-center gap-2">
                <ProgressBar
                  value={pct}
                  label={cs.display_name}
                  sublabel={`${pct.toFixed(1)}%`}
                  color={
                    isTopBar
                      ? undefined
                      : pct >= 70
                        ? "var(--color-green)"
                        : pct >= 40
                          ? "var(--color-yellow)"
                          : "var(--color-surface2)"
                  }
                  className="flex-1"
                />
                {hasPenalty && (
                  <span
                    className="text-[10px] text-red shrink-0"
                    title={`Penalty: -${(cs.penalty * 100).toFixed(0)}%`}
                  >
                    -{(cs.penalty * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Narrative */}
      {diagnosis.llm_narrative && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-text flex items-center gap-2">
            <span className="w-1 h-4 bg-primary rounded-full" />
            Analysis Narrative
          </h4>
          <div className="bg-surface0 rounded-lg p-4 text-sm text-subtext leading-relaxed border border-surface1">
            {diagnosis.llm_narrative}
          </div>
        </div>
      )}

      {/* Report text (collapsed) */}
      <details className="group">
        <summary className="text-sm font-semibold text-text cursor-pointer flex items-center gap-2 select-none">
          <span className="w-1 h-4 bg-secondary rounded-full" />
          Full Report
          <span className="text-xs text-overlay0 group-open:hidden">
            (click to expand)
          </span>
        </summary>
        <pre className="mt-2 bg-surface0 rounded-lg p-4 text-xs text-subtext overflow-x-auto border border-surface1 whitespace-pre-wrap font-mono">
          {diagnosis.report_text}
        </pre>
      </details>

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <Button size="sm" onClick={handleExport}>
          <Download size={14} />
          Export Report
        </Button>
      </div>
    </div>
  );
}
