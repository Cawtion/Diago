import { Activity, Menu, Home, Stethoscope } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { useAppStore } from "@/stores/appStore";

export function Header() {
  const location = useLocation();
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);
  const isHome = location.pathname === "/";
  const isDiagnose = location.pathname === "/diagnose";

  return (
    <header className="flex items-center justify-between px-5 py-3 border-b border-surface1 bg-mantle">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Menu size={18} />
        </Button>
        <Link
          to="/"
          className="flex items-center gap-2.5 text-text no-underline hover:opacity-90"
        >
          <div className="p-1.5 bg-primary/15 rounded-lg">
            <Activity size={22} className="text-primary" />
          </div>
          <div>
            <h1 className="text-base font-bold leading-tight">Diago</h1>
            <p className="text-[11px] text-subtext leading-tight">
              Physics-Aware Automotive Diagnostics
            </p>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-2 text-xs text-overlay0">
        {isDiagnose && (
          <Link to="/">
            <Button variant="ghost" size="sm">
              <Home size={14} />
              Home
            </Button>
          </Link>
        )}
        {isHome && (
          <Link to="/diagnose">
            <Button variant="default" size="sm">
              <Stethoscope size={14} />
              Diagnose
            </Button>
          </Link>
        )}
        <span className="hidden sm:inline">v0.1.0</span>
      </div>
    </header>
  );
}
