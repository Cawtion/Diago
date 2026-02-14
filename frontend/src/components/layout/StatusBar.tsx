import { Database, Hash, Wifi, WifiOff, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { healthCheck, getSignatureStats } from "@/lib/api";

export function StatusBar() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: healthCheck,
    refetchInterval: 30_000,
    retry: 1,
  });

  const stats = useQuery({
    queryKey: ["signatureStats"],
    queryFn: getSignatureStats,
    refetchInterval: 60_000,
    retry: 1,
  });

  const isConnected = health.data?.status === "ok";
  const healthLoading = health.isLoading || health.isFetching;
  const healthError = health.isError;

  return (
    <footer className="flex flex-wrap items-center justify-between gap-2 px-3 sm:px-4 py-1.5 border-t border-surface1 bg-mantle text-xs text-overlay0">
      <div className="flex flex-wrap items-center gap-3 sm:gap-4">
        <span className="flex items-center gap-1.5">
          {healthLoading ? (
            <Loader2 size={12} className="animate-spin text-primary" />
          ) : isConnected ? (
            <Wifi size={12} className="text-secondary" />
          ) : (
            <WifiOff size={12} className="text-red" />
          )}
          {healthLoading
            ? "Connecting…"
            : healthError
              ? "API error"
              : isConnected
                ? "API Connected"
                : "API Offline"}
        </span>
        {stats.isLoading ? null : stats.data ? (
          <>
            <span className="flex items-center gap-1.5">
              <Database size={12} />
              {stats.data.total_signatures} signatures
            </span>
            <span className="flex items-center gap-1.5">
              <Hash size={12} />
              {stats.data.total_hashes} hashes
            </span>
          </>
        ) : null}
      </div>
      <span className="hidden sm:inline">
        Diago v{health.data?.version ?? "?"}
      </span>
    </footer>
  );
}
