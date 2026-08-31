"use client";

import { useState } from "react";
import Header from "@/components/common/Header";
import { ShieldCheck, Zap, Car, BarChart3 } from "lucide-react";
import AiInsightsFeed from "@/components/analysis/AiInsightsFeed";
import LiveRoadDetail from "@/components/analysis/LiveRoadDetail";
import SystemSnapshot from "@/components/analysis/SystemSnapshot";
import PerformanceMetrics from "@/components/analysis/PerformanceMetrics";
import CongestionBreakdown from "@/components/traffic/CongestionBreakdown";
import { useTraffixContext } from "@/context/TraffixContext";
import { useLiveKpi } from "@/hooks/useLiveData";

type AnalysisTab = "overview" | "road" | "snapshot" | "metrics";

const TABS: { id: AnalysisTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "road", label: "Live Road Detail" },
  { id: "snapshot", label: "System Snapshot" },
  { id: "metrics", label: "Full Metrics Table" },
];

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState<AnalysisTab>("overview");

  const { edges, missions } = useTraffixContext();
  const { kpi } = useLiveKpi(edges);

  // Real, current-state KPI strip — replaces four hardcoded percentages
  // ("−41.6%", "+75.0%", ...) that implied a measured before/after
  // deployment comparison which was never actually run. These are the
  // real network's numbers right now.
  const kpiCards = [
    {
      label: "Network Health",
      value: `${kpi.networkHealthPct}%`,
      icon: Zap,
      color: "text-emerald-600",
      bg: "bg-emerald-50 border-emerald-100 text-emerald-600",
    },
    {
      label: "Active Vehicles",
      value: kpi.activeVehicles.toLocaleString(),
      icon: Car,
      color: "text-sky-600",
      bg: "bg-sky-50 border-sky-100 text-sky-600",
    },
    {
      label: "High-Risk Segments",
      value: String(kpi.highCount + kpi.congestedCount),
      icon: ShieldCheck,
      color: "text-red-600",
      bg: "bg-red-50 border-red-100 text-red-600",
    },
    {
      label: "Active Emergency Missions",
      value: String(missions.length),
      icon: ShieldCheck,
      color: "text-amber-600",
      bg: "bg-amber-50 border-amber-100 text-amber-600",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-sky-500" />
            Analysis &amp; Reasoning
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            The real, current state of the Anna Nagar network — live XGBoost risk scoring, real
            accidents and emergency missions, and real per-edge congestion. No fabricated
            before/after comparisons: where a real baseline or forecast model doesn&apos;t exist in
            this deployment, that&apos;s said plainly rather than invented.
          </p>
        </div>

        {/* KPI strip — real, current-state numbers */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiCards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.label}
                className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3"
              >
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center border ${card.bg}`}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    {card.label}
                  </span>
                  <span className={`text-lg font-extrabold ${card.color}`}>
                    {card.value}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1 shadow-sm w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === tab.id
                  ? "bg-sky-500 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-6">
            <AiInsightsFeed />
            <CongestionBreakdown
              lowCount={kpi.lowCount}
              moderateCount={kpi.moderateCount}
              highCount={kpi.highCount}
              congestedCount={kpi.congestedCount}
            />
          </div>
        )}

        {activeTab === "road" && <LiveRoadDetail />}

        {activeTab === "snapshot" && <SystemSnapshot />}

        {activeTab === "metrics" && <PerformanceMetrics />}
      </main>
    </div>
  );
}
