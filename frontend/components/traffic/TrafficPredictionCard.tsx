"use client";

import { useState, useEffect } from "react";
import { TrendingUp, ShieldCheck, Cpu, RefreshCw } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  fetchTrafficForecast,
  PredictionHorizon,
  ForecastPoint,
} from "@/services/predictionApi";
import { useTraffixContext } from "@/context/TraffixContext";

type HorizonOption = { label: string; value: PredictionHorizon };

const HORIZONS: HorizonOption[] = [
  { label: "+15m", value: "15min" },
  { label: "+30m", value: "30min" },
  { label: "+1hr", value: "60min" },
  { label: "+2hr", value: "120min" },
];

const ROAD_OPTIONS = [
  { id: "road_anna_2", label: "Anna Salai (Teynampet)" },
  { id: "road_mount_1", label: "Mount Flyover Jn" },
  { id: "road_ring_2",  label: "Guindy Ring Road" },
];

export default function TrafficPredictionCard() {
  const { wsStep } = useTraffixContext();
  const [horizon, setHorizon] = useState<PredictionHorizon>("30min");
  const [roadId, setRoadId] = useState("road_anna_2");
  const [points, setPoints] = useState<ForecastPoint[]>([]);
  const [confidence, setConfidence] = useState(94.8);
  const [modelVersion, setModelVersion] = useState("XGBoost v15");
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<number>(0);

  const loadForecast = async () => {
    setLoading(true);
    try {
      const res = await fetchTrafficForecast(roadId, horizon);
      setPoints(res.points);
      setConfidence(parseFloat((res.overallConfidence * 100).toFixed(1)));
      setModelVersion(res.modelVersion);
      setLastUpdated(wsStep);
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when horizon or road changes
  useEffect(() => { loadForecast(); }, [horizon, roadId]);

  // Auto-refresh every 30 WS steps
  useEffect(() => {
    if (wsStep > 0 && wsStep % 30 === 0) loadForecast();
  }, [wsStep]);

  const chartData = points.map((p) => ({
    time: p.timeLabel,
    current: p.currentDensity,
    forecast: p.predictedDensity,
    historical: p.historicalDensity,
  }));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-sky-500" />
          <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wide">
            Traffic Density & Risk Prediction
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {/* Road selector */}
          <select
            value={roadId}
            onChange={(e) => setRoadId(e.target.value)}
            className="text-[10px] font-bold bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-slate-700"
          >
            {ROAD_OPTIONS.map((r) => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </select>

          {/* Horizon filter */}
          <div className="flex items-center gap-0.5 bg-slate-100 p-0.5 rounded-lg text-[10px] font-bold">
            {HORIZONS.map((h) => (
              <button
                key={h.value}
                onClick={() => setHorizon(h.value)}
                className={`px-2 py-0.5 rounded transition-all ${
                  horizon === h.value
                    ? "bg-white text-sky-600 shadow-xs"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>

          {/* Refresh */}
          <button
            onClick={loadForecast}
            disabled={loading}
            className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-all disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Model meta cards */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-sky-50/70 p-2.5 rounded-lg border border-sky-200/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-sky-700 uppercase block">Model</span>
            <span className="font-extrabold text-sky-950 text-sm">{modelVersion}</span>
          </div>
          <Cpu className="w-5 h-5 text-sky-500 opacity-80" />
        </div>
        <div className="bg-emerald-50/70 p-2.5 rounded-lg border border-emerald-200/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-emerald-700 uppercase block">Confidence</span>
            <span className="font-extrabold text-emerald-950 text-sm">{confidence}%</span>
          </div>
          <ShieldCheck className="w-5 h-5 text-emerald-500 opacity-80" />
        </div>
      </div>

      {/* Area Chart */}
      <div className="h-[220px] w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="currentGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={10} tickLine={false} tickFormatter={(v) => `${v}%`} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderRadius: "8px",
                border: "none",
                color: "#fff",
                fontSize: "11px",
              }}
            />
            <Area type="monotone" dataKey="historical" stroke="#94a3b8" strokeWidth={1.5} fillOpacity={1} fill="url(#histGrad)" name="Historical" dot={false} />
            <Area type="monotone" dataKey="current" stroke="#0ea5e9" strokeWidth={2} fillOpacity={1} fill="url(#currentGrad)" name="Current" dot={false} />
            <Area type="monotone" dataKey="forecast" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#forecastGrad)" name="XGBoost Forecast" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-100 pt-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-semibold text-slate-400"><span className="w-2 h-2 rounded-full bg-slate-400" /> Historical</span>
          <span className="flex items-center gap-1 font-semibold text-sky-600"><span className="w-2 h-2 rounded-full bg-sky-500" /> Current</span>
          <span className="flex items-center gap-1 font-semibold text-amber-600"><span className="w-2 h-2 rounded-full bg-amber-500" /> Forecast</span>
        </div>
        <span className="font-mono">
          {lastUpdated > 0 ? `Step #${lastUpdated}` : "Loading…"}
        </span>
      </div>
    </div>
  );
}
