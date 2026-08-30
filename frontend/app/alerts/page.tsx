"use client";

import { useMemo, useState } from "react";
import Header from "@/components/common/Header";
import { IntelligenceMessage } from "@/types/common";
import { AlertSeverity, AlertCategory } from "@/types/alerts";
import { useTraffixContext } from "@/context/TraffixContext";
import {
  Bell,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  X,
  Check,
  Radio,
  Filter,
} from "lucide-react";

// ── severity config ──────────────────────────────────────────────────────────
const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { label: string; card: string; badge: string; icon: React.ReactNode }
> = {
  critical: {
    label: "Critical",
    card: "bg-red-50 border-red-200",
    badge: "bg-red-100 text-red-700 border-red-200",
    icon: <ShieldAlert className="w-4 h-4 text-red-600" />,
  },
  warning: {
    label: "Warning",
    card: "bg-amber-50 border-amber-200",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
    icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
  },
  info: {
    label: "Info",
    card: "bg-sky-50 border-sky-200",
    badge: "bg-sky-100 text-sky-700 border-sky-200",
    icon: <Info className="w-4 h-4 text-sky-600" />,
  },
  success: {
    label: "Resolved",
    card: "bg-emerald-50 border-emerald-200",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
  },
};

const CATEGORY_LABELS: Record<AlertCategory, string> = {
  accident: "Accident",
  emergency: "Emergency",
  routing: "Routing",
  signal: "Signals",
  iot: "IoT",
  prediction: "Prediction",
  system: "System",
};

const CATEGORY_COLORS: Record<AlertCategory, string> = {
  accident: "bg-red-100 text-red-700 border-red-200",
  emergency: "bg-rose-100 text-rose-700 border-rose-200",
  routing: "bg-sky-100 text-sky-700 border-sky-200",
  signal: "bg-violet-100 text-violet-700 border-violet-200",
  iot: "bg-indigo-100 text-indigo-700 border-indigo-200",
  prediction: "bg-purple-100 text-purple-700 border-purple-200",
  system: "bg-slate-100 text-slate-600 border-slate-200",
};

// Real IntelligenceMessage.type -> the display severity/category here.
// Never invented: derived directly from the same type/urgent fields the
// live message feed (MessageBox) already uses (see useLiveData.ts).
function severityOf(m: IntelligenceMessage): AlertSeverity {
  if (m.type === "warning") return "warning";
  if (m.type === "success") return "success";
  if ((m.type === "accident" || m.type === "emergency") && m.urgent) return "critical";
  return "info";
}

function categoryOf(m: IntelligenceMessage): AlertCategory {
  if (m.type === "accident" || m.type === "emergency" || m.type === "routing" || m.type === "system") {
    return m.type;
  }
  return "system";
}

type SeverityFilter = AlertSeverity | "all";

const SEVERITY_FILTERS: { id: SeverityFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "critical", label: "Critical" },
  { id: "warning", label: "Warning" },
  { id: "info", label: "Info" },
  { id: "success", label: "Resolved" },
];

export default function AlertsPage() {
  const { messages, acknowledgeMessage, dismissMessage, acknowledgeAllMessages } = useTraffixContext();
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [showDismissed, setShowDismissed] = useState(false);

  // ── derived counts — real, from the same live message log everywhere
  // else in the app reads (the ALERTS nav badge, MessageBox) ─────────────
  const counts = useMemo(() => {
    const active = messages.filter((m) => !m.dismissed);
    return {
      total: active.length,
      critical: active.filter((m) => severityOf(m) === "critical").length,
      warning: active.filter((m) => severityOf(m) === "warning").length,
      unacked: active.filter((m) => !m.acknowledged).length,
    };
  }, [messages]);

  const visible = useMemo(() => {
    return messages.filter((m) => {
      if (!showDismissed && m.dismissed) return false;
      if (severityFilter !== "all" && severityOf(m) !== severityFilter) return false;
      return true;
    });
  }, [messages, severityFilter, showDismissed]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Bell className="w-6 h-6 text-sky-500" />
              Alerts Center
              {counts.unacked > 0 && (
                <span className="inline-flex items-center justify-center w-6 h-6 bg-red-500 text-white text-xs font-extrabold rounded-full animate-pulse">
                  {counts.unacked}
                </span>
              )}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              The same real event log MessageBox shows — accidents, routing, missions, and system
              events, actually pushed as they happen. Nothing here is a canned scenario.
            </p>
          </div>

          <button
            onClick={acknowledgeAllMessages}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-xl text-xs font-bold transition-all"
          >
            <Check className="w-3.5 h-3.5" />
            Acknowledge All
          </button>
        </div>

        {/* Summary strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Active", value: counts.total, color: "text-slate-900", bg: "bg-white border-slate-200" },
            { label: "Critical", value: counts.critical, color: "text-red-700", bg: "bg-red-50 border-red-200" },
            { label: "Warnings", value: counts.warning, color: "text-amber-700", bg: "bg-amber-50 border-amber-200" },
            { label: "Unacknowledged", value: counts.unacked, color: "text-sky-700", bg: "bg-sky-50 border-sky-200" },
          ].map((s) => (
            <div key={s.label} className={`${s.bg} rounded-xl border p-4 shadow-sm`}>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{s.label}</p>
              <p className={`text-3xl font-black mt-1 tabular-nums ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1 shadow-sm">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
            {SEVERITY_FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => setSeverityFilter(f.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  severityFilter === f.id
                    ? "bg-sky-500 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowDismissed((v) => !v)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-bold transition-all ${
              showDismissed
                ? "bg-slate-700 text-white border-slate-700"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            {showDismissed ? "Hide Dismissed" : "Show Dismissed"}
          </button>

          <span className="text-xs text-slate-400 font-medium ml-auto">
            Showing {visible.length} alert{visible.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Alert feed */}
        <div className="flex flex-col gap-3">
          {visible.length === 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center text-slate-400 text-sm font-semibold shadow-sm">
              <CheckCircle2 className="w-8 h-8 mx-auto mb-3 text-emerald-400" />
              {messages.length === 0
                ? "No events yet — they'll appear here as they really happen."
                : "No alerts match the current filter."}
            </div>
          )}

          {visible.map((m) => {
            const severity = severityOf(m);
            const category = categoryOf(m);
            const cfg = SEVERITY_CONFIG[severity];
            return (
              <div
                key={m.id}
                className={`rounded-xl border shadow-sm overflow-hidden transition-all ${cfg.card} ${
                  m.dismissed ? "opacity-50" : ""
                }`}
              >
                <div className="p-4 flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">{cfg.icon}</div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-extrabold text-slate-900">{m.text}</span>
                        {!m.acknowledged && !m.dismissed && (
                          <span className="px-1.5 py-0.5 bg-red-500 text-white text-[10px] font-extrabold rounded-full">
                            NEW
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-slate-400 flex-shrink-0">{m.timestamp}</span>
                    </div>

                    {m.details && <p className="text-xs text-slate-600 mt-1 leading-relaxed">{m.details}</p>}

                    <div className="mt-2.5 flex items-center gap-2 flex-wrap">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${cfg.badge}`}>
                        {cfg.label}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${CATEGORY_COLORS[category]}`}>
                        {CATEGORY_LABELS[category]}
                      </span>
                      <span className="flex items-center gap-1 text-[10px] text-slate-400">
                        <Radio className="w-3 h-3" />
                        TRAFFIX Live Feed
                      </span>
                      {m.acknowledged && !m.dismissed && (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-600 font-bold ml-auto">
                          <CheckCircle2 className="w-3 h-3" />
                          Acknowledged
                        </span>
                      )}
                    </div>
                  </div>

                  {!m.dismissed && (
                    <div className="flex flex-col gap-1.5 flex-shrink-0">
                      {!m.acknowledged && (
                        <button
                          onClick={() => acknowledgeMessage(m.id)}
                          title="Acknowledge"
                          className="w-7 h-7 flex items-center justify-center rounded-lg bg-emerald-100 hover:bg-emerald-200 text-emerald-700 border border-emerald-200 transition-all"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => dismissMessage(m.id)}
                        title="Dismiss"
                        className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 border border-slate-200 transition-all"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
