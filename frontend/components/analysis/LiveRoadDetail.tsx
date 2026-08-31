"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Search, Gauge, Activity } from "lucide-react";
import { loadRealLocations } from "@/services/navigationApi";
import { LocationSuggestion } from "@/types/route";
import { useTraffixContext } from "@/context/TraffixContext";

// How many real observed ticks to keep for the session trend line — ~3
// minutes at the real 1 Hz broadcast rate. This is genuinely observed data
// accumulated client-side while this tab is open, never a forecast or a
// canned series (there is no real forecasting model in this deployment).
const MAX_HISTORY_POINTS = 180;

interface HistoryPoint {
  tick: number;
  congestionPct: number;
  riskPct: number;
  speed: number;
}

export default function LiveRoadDetail() {
  const { edges, wsStep, wsConnected } = useTraffixContext();

  const [locations, setLocations] = useState<LocationSuggestion[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<LocationSuggestion | null>(null);
  const [locError, setLocError] = useState<string | null>(null);
  const historyRef = useRef<HistoryPoint[]>([]);
  const [history, setHistory] = useState<HistoryPoint[]>([]);

  useEffect(() => {
    loadRealLocations()
      .then(setLocations)
      .catch(() => setLocError("Real network location data unavailable."));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return locations.slice(0, 8);
    return locations.filter((l) => l.name.toLowerCase().includes(q)).slice(0, 8);
  }, [query, locations]);

  const liveEdge = useMemo(
    () => (selected ? edges.find((e) => e.edge_id === selected.edge_id) ?? null : null),
    [edges, selected]
  );

  // Accumulate a genuinely real, observed-this-session trend for the
  // selected road — reset whenever the selected road changes.
  useEffect(() => {
    historyRef.current = [];
    setHistory([]);
  }, [selected?.edge_id]);

  useEffect(() => {
    if (!liveEdge || wsStep === undefined) return;
    const next: HistoryPoint = {
      tick: wsStep,
      congestionPct: Math.round(liveEdge.congestion_score * 100),
      riskPct: Math.round(liveEdge.risk_score * 100),
      speed: liveEdge.speed,
    };
    const arr = historyRef.current;
    if (arr.length === 0 || arr[arr.length - 1].tick !== next.tick) {
      const updated = [...arr, next].slice(-MAX_HISTORY_POINTS);
      historyRef.current = updated;
      setHistory(updated);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsStep, liveEdge?.congestion_score, liveEdge?.risk_score, liveEdge?.speed]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Live Road Detail</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Pick a real Anna Nagar road — no forecast model exists in this deployment, so this
            shows the real current state plus what&apos;s actually been observed this session.
          </p>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Search */}
        <div className="relative max-w-sm">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search a real street name..."
            className="w-full pl-8 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-400"
          />
        </div>

        {locError && <p className="text-xs text-red-600 font-semibold">{locError}</p>}

        {!selected && (
          <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto">
            {filtered.length === 0 && !locError && (
              <p className="text-xs text-slate-400 py-2">
                {locations.length === 0 ? "Loading real network locations…" : "No matching street found."}
              </p>
            )}
            {filtered.map((loc) => (
              <button
                key={loc.edge_id}
                onClick={() => setSelected(loc)}
                className="text-left p-2.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-sky-50 hover:border-sky-300 transition-all text-xs font-bold text-slate-700"
              >
                {loc.name}
              </button>
            ))}
          </div>
        )}

        {selected && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-extrabold text-slate-900">{selected.name}</span>
              <button
                onClick={() => setSelected(null)}
                className="text-[10px] font-bold text-sky-600 hover:text-sky-800"
              >
                Change road
              </button>
            </div>

            {!wsConnected && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2.5 font-semibold">
                Live stream offline — values below are the last known state, not live.
              </p>
            )}

            {!liveEdge ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                Waiting for this edge in the live stream…
              </p>
            ) : (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <StatCard icon={Gauge} label="Speed" value={`${liveEdge.speed.toFixed(1)} km/h`} color="sky" />
                  <StatCard icon={Activity} label="Vehicles" value={String(liveEdge.vehicle_count)} color="violet" />
                  <StatCard
                    icon={Activity}
                    label="Congestion"
                    value={`${Math.round(liveEdge.congestion_score * 100)}%`}
                    color="amber"
                  />
                  <StatCard
                    icon={Activity}
                    label="V15/V16 Risk"
                    value={`${Math.round(liveEdge.risk_score * 100)}%`}
                    color="red"
                  />
                </div>

                <div>
                  <p className="text-xs font-bold text-slate-700 mb-2">
                    Observed This Session ({history.length} real tick{history.length === 1 ? "" : "s"})
                  </p>
                  {history.length < 2 ? (
                    <p className="text-xs text-slate-400 py-8 text-center border border-dashed border-slate-200 rounded-xl">
                      Keep this tab open — the chart fills in as real ticks arrive.
                    </p>
                  ) : (
                    <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <defs>
                            <linearGradient id="congGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.35} />
                              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="tick" stroke="#94a3b8" fontSize={10} tickLine={false} />
                          <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                          <Tooltip
                            contentStyle={{ backgroundColor: "#0f172a", borderRadius: "8px", border: "none", color: "#fff", fontSize: "11px" }}
                          />
                          <Area type="monotone" dataKey="congestionPct" name="Congestion %" stroke="#f59e0b" strokeWidth={2} fill="url(#congGrad)" dot={false} />
                          <Area type="monotone" dataKey="riskPct" name="Risk %" stroke="#ef4444" strokeWidth={2} fill="url(#riskGrad)" dot={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Gauge;
  label: string;
  value: string;
  color: "sky" | "violet" | "amber" | "red";
}) {
  const colorMap = {
    sky: "bg-sky-50 border-sky-200 text-sky-700",
    violet: "bg-violet-50 border-violet-200 text-violet-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700",
    red: "bg-red-50 border-red-200 text-red-700",
  } as const;
  return (
    <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${colorMap[color]}`}>
      <Icon className="w-4 h-4 opacity-80" />
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wider opacity-70">{label}</p>
        <p className="text-sm font-extrabold">{value}</p>
      </div>
    </div>
  );
}
