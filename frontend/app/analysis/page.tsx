"use client";

import { useState } from "react";
import Header from "@/components/common/Header";
import { ApplicationMode } from "@/types/common";
import {
  TrendingDown,
  Clock,
  ShieldCheck,
  Zap,
  BarChart3,
} from "lucide-react";
import TrafficPredictionCard from "@/components/traffic/TrafficPredictionCard";
import CongestionForecast from "@/components/analysis/CongestionForecast";
import InterventionScore from "@/components/analysis/InterventionScore";
import PerformanceMetrics from "@/components/analysis/PerformanceMetrics";
import SystemImpact from "@/components/analysis/SystemImpact";

const KPI_CARDS = [
  {
    label: "Travel Time Reduction",
    value: "−41.6%",
    icon: TrendingDown,
    color: "text-emerald-600",
    bg: "bg-emerald-50 border-emerald-100 text-emerald-600",
  },
  {
    label: "Average Speed Gain",
    value: "+75.0%",
    icon: Zap,
    color: "text-sky-600",
    bg: "bg-sky-50 border-sky-100 text-sky-600",
  },
  {
    label: "Risk Avoidance Rate",
    value: "81.5%",
    icon: ShieldCheck,
    color: "text-indigo-600",
    bg: "bg-indigo-50 border-indigo-100 text-indigo-600",
  },
  {
    label: "Emergency Response Time",
    value: "3.5 min",
    icon: Clock,
    color: "text-amber-600",
    bg: "bg-amber-50 border-amber-100 text-amber-600",
  },
];

type AnalysisTab = "overview" | "forecast" | "impact" | "metrics";

const TABS: { id: AnalysisTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "forecast", label: "Congestion Forecast" },
  { id: "impact", label: "System Impact" },
  { id: "metrics", label: "Full Metrics Table" },
];

export default function AnalysisPage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [activeTab, setActiveTab] = useState<AnalysisTab>("overview");

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header mode={mode} onModeChange={setMode} />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-sky-500" />
            Analysis &amp; Reasoning
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Quantified impact of TRAFFIX XGBoost risk prediction, emergency green corridors, and adaptive signal management.
          </p>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {KPI_CARDS.map((card) => {
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
            <TrafficPredictionCard />
            <InterventionScore />
          </div>
        )}

        {activeTab === "forecast" && (
          <CongestionForecast />
        )}

        {activeTab === "impact" && (
          <SystemImpact />
        )}

        {activeTab === "metrics" && (
          <PerformanceMetrics />
        )}
      </main>
    </div>
  );
}
