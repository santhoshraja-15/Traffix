"use client";

import { CheckCircle2, HeartPulse, Hospital, Clock, Star } from "lucide-react";
import { useEffect, useState } from "react";

interface RescueStatusProps {
  dispatched: boolean;
  etaSeconds: number | null;
}

type RescuePhase =
  | "idle"
  | "en-route"
  | "at-scene"
  | "patient-loaded"
  | "to-hospital"
  | "complete";

const PHASE_LABELS: Record<RescuePhase, string> = {
  idle: "Standby",
  "en-route": "Unit En Route",
  "at-scene": "Unit At Scene",
  "patient-loaded": "Patient Secured",
  "to-hospital": "En Route to Hospital",
  complete: "Rescue Successful",
};

const PHASE_ORDER: RescuePhase[] = [
  "en-route",
  "at-scene",
  "patient-loaded",
  "to-hospital",
  "complete",
];

export default function RescueStatus({ dispatched, etaSeconds }: RescueStatusProps) {
  const [phase, setPhase] = useState<RescuePhase>("idle");

  useEffect(() => {
    if (!dispatched) {
      setPhase("idle");
      return;
    }

    // Phase 1: En route immediately
    setPhase("en-route");

    // Phase 2: At scene after ETA (simulated fast for demo)
    const t1 = setTimeout(() => setPhase("at-scene"), 12000);
    const t2 = setTimeout(() => setPhase("patient-loaded"), 20000);
    const t3 = setTimeout(() => setPhase("to-hospital"), 26000);
    const t4 = setTimeout(() => setPhase("complete"), 38000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [dispatched]);

  if (!dispatched && phase === "idle") return null;

  const currentIdx = PHASE_ORDER.indexOf(phase);

  return (
    <div
      className={`bg-white rounded-xl border shadow-sm overflow-hidden transition-all ${
        phase === "complete" ? "border-emerald-300" : "border-slate-200"
      }`}
    >
      {/* Header */}
      <div
        className={`px-5 py-4 border-b flex items-center justify-between ${
          phase === "complete"
            ? "bg-emerald-50 border-emerald-100"
            : "bg-white border-slate-100"
        }`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
              phase === "complete"
                ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                : "bg-rose-50 text-rose-600 border-rose-100"
            }`}
          >
            {phase === "complete" ? (
              <Star className="w-4 h-4" />
            ) : (
              <HeartPulse className="w-4 h-4" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">Rescue Status</h3>
            <p className="text-xs text-slate-500">Live operation lifecycle tracking</p>
          </div>
        </div>
        <span
          className={`text-xs font-extrabold px-2.5 py-1 rounded-full ${
            phase === "complete"
              ? "bg-emerald-600 text-white"
              : "bg-rose-100 text-rose-700 animate-pulse"
          }`}
        >
          {PHASE_LABELS[phase]}
        </span>
      </div>

      <div className="p-5 flex flex-col gap-5">
        {/* Phase stepper */}
        <div className="flex flex-col gap-0">
          {PHASE_ORDER.map((p, idx) => {
            const done = idx < currentIdx;
            const active = idx === currentIdx;
            const isLast = idx === PHASE_ORDER.length - 1;

            return (
              <div key={p} className="flex items-start gap-3">
                {/* Icon + connector */}
                <div className="flex flex-col items-center">
                  <div
                    className={`w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${
                      done
                        ? "bg-emerald-500 border-emerald-500"
                        : active
                        ? "bg-white border-sky-500"
                        : "bg-white border-slate-200"
                    }`}
                  >
                    {done ? (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    ) : active ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-200" />
                    )}
                  </div>
                  {!isLast && (
                    <div
                      className={`w-0.5 h-6 mt-0.5 transition-all ${
                        done ? "bg-emerald-400" : "bg-slate-200"
                      }`}
                    />
                  )}
                </div>

                {/* Label */}
                <div className="pb-5 flex flex-col justify-center min-h-7">
                  <span
                    className={`text-xs font-bold transition-all ${
                      done
                        ? "text-emerald-700"
                        : active
                        ? "text-sky-700"
                        : "text-slate-400"
                    }`}
                  >
                    {PHASE_LABELS[p]}
                  </span>
                  {p === "to-hospital" && (
                    <span className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                      <Hospital className="w-3 h-3" /> Apollo Hospital, Greams Rd
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Complete banner */}
        {phase === "complete" && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-extrabold text-emerald-900">Rescue Successful</p>
              <p className="text-xs text-emerald-700 mt-0.5">
                Patient delivered to Apollo Hospital. Unit A-07 now returning to station.
              </p>
            </div>
          </div>
        )}

        {/* ETA note */}
        {etaSeconds !== null && phase === "en-route" && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Clock className="w-3 h-3" />
            <span>Unit is currently en route to incident location</span>
          </div>
        )}
      </div>
    </div>
  );
}
