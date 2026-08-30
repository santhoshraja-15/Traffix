"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Info, ShieldAlert, Sparkles } from "lucide-react";
import { fetchAiInsights, AiInsight } from "@/services/analysisApi";
import { useTraffixContext } from "@/context/TraffixContext";

// Refresh cadence — matches the simulation tick rate (1 Hz broadcast, but no
// need to hammer the endpoint that often); real backend state, polled, not
// pushed (no insight WS event exists — see FRONTEND_AUDIT.md).
const REFRESH_MS = 8000;

const SEVERITY_META: Record<
  AiInsight["severity"],
  { icon: typeof Info; className: string; label: string }
> = {
  info: { icon: Info, className: "text-slate-500 bg-slate-50 border-slate-200", label: "INFO" },
  low: { icon: Info, className: "text-sky-600 bg-sky-50 border-sky-200", label: "LOW" },
  medium: { icon: AlertTriangle, className: "text-amber-600 bg-amber-50 border-amber-200", label: "MEDIUM" },
  high: { icon: AlertTriangle, className: "text-orange-600 bg-orange-50 border-orange-200", label: "HIGH" },
  critical: { icon: ShieldAlert, className: "text-red-600 bg-red-50 border-red-200", label: "CRITICAL" },
};

/**
 * Real AI insight feed — GET /analysis/insights, derived entirely from the
 * live per-edge traffic state (app/services/analytics_service.py). Replaces
 * the old page that called this same endpoint but the endpoint itself
 * returned two hardcoded insights naming roads that don't exist in the real
 * network; both sides are now real (see the Phase 10 commit).
 */
export default function AiInsightsFeed() {
  const { wsConnected } = useTraffixContext();
  const [insights, setInsights] = useState<AiInsight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const result = await fetchAiInsights();
        if (!cancelled) {
          setInsights(result);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("AI insight service unavailable.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-sky-500" />
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">Live AI Insights</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Real-time, derived from the live per-edge congestion state — not a canned script
            </p>
          </div>
        </div>
        <span
          className={`text-[10px] font-bold px-2 py-1 rounded-full border ${
            wsConnected
              ? "text-emerald-700 bg-emerald-50 border-emerald-200"
              : "text-slate-500 bg-slate-50 border-slate-200"
          }`}
        >
          {wsConnected ? "SUMO Stream Active" : "Stream Offline"}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-2.5">
        {loading && <p className="text-xs text-slate-400 text-center py-6">Loading real insights…</p>}
        {!loading && error && (
          <p className="text-xs text-red-600 font-semibold text-center py-6">{error}</p>
        )}
        {!loading &&
          !error &&
          insights.map((insight) => {
            const meta = SEVERITY_META[insight.severity] ?? SEVERITY_META.info;
            const Icon = meta.icon;
            return (
              <div
                key={insight.insight_id}
                className={`p-3 rounded-xl border flex items-start gap-3 ${meta.className}`}
              >
                <Icon className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-extrabold text-slate-900">{insight.title}</span>
                    <span className="text-[9px] font-bold uppercase tracking-wider opacity-70 shrink-0">
                      {meta.label}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-1">{insight.description}</p>
                  <p className="text-[11px] text-slate-500 mt-1 italic">{insight.recommendation}</p>
                  {insight.estimated_delay > 0 && (
                    <p className="text-[10px] text-slate-400 mt-1 font-semibold">
                      Est. delay impact: ~{Math.round(insight.estimated_delay)}s
                    </p>
                  )}
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
