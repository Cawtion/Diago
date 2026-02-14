import { useCallback, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Stethoscope,
  BarChart3,
  MessageSquare,
  Play,
  Loader2,
} from "lucide-react";

import { Header } from "@/components/layout/Header";
import { StatusBar } from "@/components/layout/StatusBar";
import { Toast } from "@/components/ui/Toast";
import { RecordPanel } from "@/components/panels/RecordPanel";
import { SpectrogramView } from "@/components/panels/SpectrogramView";
import { ContextForm } from "@/components/panels/ContextForm";
import { TroubleCodePanel } from "@/components/panels/TroubleCodePanel";
import { VehiclePanel } from "@/components/panels/VehiclePanel";
import { ResultsPanel } from "@/components/panels/ResultsPanel";
import { ChatPanel } from "@/components/panels/ChatPanel";
import { SessionHistory } from "@/components/panels/SessionHistory";
import { Tabs } from "@/components/ui/Tabs";
import { Button } from "@/components/ui/Button";
import { useAppStore } from "@/stores/appStore";
import { useToastStore } from "@/stores/toastStore";
import { diagnoseAudio, diagnoseText } from "@/lib/api";
import { cn } from "@/lib/utils";

const BOTTOM_TABS = [
  {
    id: "symptoms",
    label: "Symptoms & Codes",
    icon: <Stethoscope size={14} />,
  },
  { id: "results", label: "Results", icon: <BarChart3 size={14} /> },
  { id: "chat", label: "DiagBot", icon: <MessageSquare size={14} /> },
];

export function DiagnoseView() {
  const location = useLocation();
  const navigate = useNavigate();
  const vehicleSectionRef = useRef<HTMLDivElement>(null);

  const {
    activeTab,
    setActiveTab,
    audioBlob,
    symptoms,
    activeCodes,
    context,
    isDiagnosing,
    setIsDiagnosing,
    setDiagnosis,
    sidebarOpen,
    setSidebarOpen,
  } = useAppStore();

  const toast = useToastStore((s) => s.show);

  /* Focus vehicle: open Symptoms tab and scroll to VehiclePanel */
  useEffect(() => {
    const focus = (location.state as { focus?: string } | null)?.focus;
    if (focus === "vehicle") {
      setActiveTab("symptoms");
      const t = setTimeout(() => {
        vehicleSectionRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
        navigate("/diagnose", { replace: true, state: {} });
      }, 150);
      return () => clearTimeout(t);
    }
  }, [location.state, setActiveTab, navigate]);

  const handleAnalyze = useCallback(async () => {
    setIsDiagnosing(true);
    try {
      let result;
      if (audioBlob) {
        result = await diagnoseAudio(
          audioBlob,
          symptoms,
          activeCodes.join(",")
        );
      } else {
        result = await diagnoseText({
          symptoms,
          codes: activeCodes,
          context,
        });
      }
      setDiagnosis(result);
      setActiveTab("results");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      console.error("Diagnosis failed:", e);
      toast(`Diagnosis failed: ${msg}`, "error");
    } finally {
      setIsDiagnosing(false);
    }
  }, [
    audioBlob,
    symptoms,
    activeCodes,
    context,
    toast,
    setIsDiagnosing,
    setDiagnosis,
    setActiveTab,
  ]);

  return (
    <div className="h-full flex flex-col min-h-0">
      <Header />
      <Toast />
      <RecordPanel />

      <div className="flex-1 flex min-h-0 overflow-hidden">
        <div className="flex-1 flex flex-col min-w-0">
          <SpectrogramView />

          <div className="flex items-center justify-center px-3 sm:px-4 py-2 border-y border-surface1">
            <Button
              variant="primary"
              size="lg"
              onClick={handleAnalyze}
              disabled={
                isDiagnosing ||
                (!audioBlob && !symptoms && activeCodes.length === 0)
              }
              className="w-full sm:w-auto min-w-[140px]"
            >
              {isDiagnosing ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Analyze
                </>
              )}
            </Button>
          </div>

          <Tabs
            tabs={BOTTOM_TABS}
            activeTab={activeTab}
            onTabChange={(id) =>
              setActiveTab(id as "symptoms" | "results" | "chat")
            }
          />

          <div className="flex-1 min-h-0 overflow-y-auto">
            {activeTab === "symptoms" && (
              <div className="p-3 sm:p-4 md:p-5 space-y-5 md:space-y-6">
                <div ref={vehicleSectionRef}>
                  <VehiclePanel />
                </div>
                <ContextForm />
                <TroubleCodePanel />
              </div>
            )}
            {activeTab === "results" && <ResultsPanel />}
            {activeTab === "chat" && <ChatPanel />}
          </div>
        </div>

        <aside
          className={cn(
            "w-80 border-l border-surface1 bg-mantle flex-col",
            "hidden lg:flex"
          )}
        >
          <SessionHistory />
        </aside>

        {sidebarOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/50 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <aside className="fixed right-0 top-0 bottom-0 w-80 bg-mantle border-l border-surface1 z-50 flex flex-col lg:hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-surface1">
                <span className="text-sm font-semibold text-text">
                  Session History
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(false)}
                >
                  ✕
                </Button>
              </div>
              <SessionHistory />
            </aside>
          </>
        )}
      </div>

      <StatusBar />
    </div>
  );
}
