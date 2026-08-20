"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

const HOURS = [
  "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
  "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
  "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
  "18:00", "19:00", "20:00", "21:00", "22:00", "23:00",
];

const ANNA_SALAI = [8,5,4,3,4,10,32,74,88,72,58,63,61,55,60,68,82,91,78,56,38,26,18,11];
const MOUNT_RD   = [5,3,2,2,3,7,24,68,82,65,51,56,54,48,53,61,76,88,71,49,33,22,14,8];
const GUINDY     = [6,4,3,2,3,8,28,71,85,68,54,60,58,52,57,65,80,90,74,53,35,24,16,9];

const DATA = HOURS.map((h, i) => ({
  time: h,
  "Anna Salai": ANNA_SALAI[i],
  "Mount Rd": MOUNT_RD[i],
  "Guindy Ring": GUINDY[i],
}));

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 rounded-xl px-4 py-3 shadow-xl border border-slate-700 text-xs">
      <p className="font-bold text-slate-300 mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.dataKey}:</span>
          <span className="font-bold text-white">{p.value}%</span>
        </div>
      ))}
    </div>
  );
};

export default function CongestionForecast() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">24-Hour Congestion Forecast</h3>
          <p className="text-xs text-slate-500 mt-0.5">Road occupancy % across major corridors — XGBoost v15 projection</p>
        </div>
        <span className="text-xs font-bold text-violet-700 bg-violet-50 border border-violet-200 px-2.5 py-1 rounded-full">
          XGBoost v15 · 94.8% conf.
        </span>
      </div>

      <div className="p-5">
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DATA} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="gAnna" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gMount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gGuindy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                fontSize={10}
                tickLine={false}
                interval={3}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={10}
                tickLine={false}
                tickFormatter={(v) => `${v}%`}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: "11px", paddingTop: "12px" }}
              />
              <Area
                type="monotone"
                dataKey="Anna Salai"
                stroke="#0ea5e9"
                strokeWidth={2}
                fill="url(#gAnna)"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="Mount Rd"
                stroke="#8b5cf6"
                strokeWidth={2}
                fill="url(#gMount)"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="Guindy Ring"
                stroke="#f59e0b"
                strokeWidth={2}
                fill="url(#gGuindy)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Peak annotation */}
        <div className="mt-4 flex flex-wrap gap-3">
          {[
            { road: "Anna Salai", peak: "17:00 — 91%", color: "text-sky-600 bg-sky-50 border-sky-200" },
            { road: "Mount Rd", peak: "17:00 — 88%", color: "text-violet-600 bg-violet-50 border-violet-200" },
            { road: "Guindy Ring", peak: "17:00 — 90%", color: "text-amber-600 bg-amber-50 border-amber-200" },
          ].map((item) => (
            <div
              key={item.road}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold ${item.color}`}
            >
              <span>{item.road}</span>
              <span className="opacity-60">·</span>
              <span>Peak {item.peak}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
