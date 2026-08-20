"use client";

import { useState, useEffect } from "react";
import { Ambulance, MapPin, Clock, CheckCircle2, Radio, Navigation } from "lucide-react";

interface AmbulanceUnit {
  id: string;
  callSign: string;
  status: "available" | "dispatched" | "at-scene" | "returning";
  location: string;
  distanceKm: number;
  etaMin: number;
  crew: string;
  hospital: string;
}

const UNITS: AmbulanceUnit[] = [
  {
    id: "amb-a07",
    callSign: "A-07",
    status: "available",
    location: "Nungambakkam Station",
    distanceKm: 1.4,
    etaMin: 3,
    crew: "Dr. Rajan Kumar + Paramedic",
    hospital: "Apollo Hospital, Greams Rd",
  },
  {
    id: "amb-b12",
    callSign: "B-12",
    status: "available",
    location: "Kodambakkam Hub",
    distanceKm: 2.8,
    etaMin: 6,
    crew: "Dr. Priya Srinivasan + Paramedic",
    hospital: "MIOT International, Manapakkam",
  },
  {
    id: "amb-c03",
    callSign: "C-03",
    status: "at-scene",
    location: "Guindy Industrial Estate",
    distanceKm: 4.1,
    etaMin: 9,
    crew: "Dr. Arjun Menon + Paramedic",
    hospital: "Fortis Malar, Adyar",
  },
];

const STATUS_COLORS: Record<AmbulanceUnit["status"], string> = {
  available: "bg-emerald-100 text-emerald-700 border-emerald-200",
  dispatched: "bg-sky-100 text-sky-700 border-sky-200",
  "at-scene": "bg-amber-100 text-amber-700 border-amber-200",
  returning: "bg-slate-100 text-slate-600 border-slate-200",
};

const STATUS_LABELS: Record<AmbulanceUnit["status"], string> = {
  available: "Available",
  dispatched: "Dispatched",
  "at-scene": "At Scene",
  returning: "Returning",
};

interface AmbulancePanelProps {
  incidentActive: boolean;
  onDispatch: (unitId: string) => void;
  dispatchedUnitId: string | null;
}

export default function AmbulancePanel({
  incidentActive,
  onDispatch,
  dispatchedUnitId,
}: AmbulancePanelProps) {
  const [selectedUnit, setSelectedUnit] = useState<string>("amb-a07");
  const [etaCountdown, setEtaCountdown] = useState<number | null>(null);

  const dispatched = dispatchedUnitId !== null;
  const dispatchedUnit = UNITS.find((u) => u.id === dispatchedUnitId);

  // Start countdown after dispatch
  useEffect(() => {
    if (!dispatched) return;
    const unit = UNITS.find((u) => u.id === dispatchedUnitId);
    if (!unit) return;
    setEtaCountdown(unit.etaMin * 60);
    const interval = setInterval(() => {
      setEtaCountdown((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [dispatched, dispatchedUnitId]);

  const formatCountdown = (secs: number) => {
    const m = Math.floor(secs / 60)
      .toString()
      .padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
            <Ambulance className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">Ambulance Dispatch Command</h3>
            <p className="text-xs text-slate-500">Nearest available unit assignment</p>
          </div>
        </div>
        {dispatched && (
          <span className="px-2.5 py-1 bg-sky-500 text-white text-xs font-bold rounded-full animate-pulse">
            UNIT DISPATCHED
          </span>
        )}
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Dispatched status card */}
        {dispatched && dispatchedUnit && etaCountdown !== null && (
          <div className="p-4 bg-sky-50 border border-sky-200 rounded-xl flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-sky-600 animate-pulse" />
              <span className="text-xs font-extrabold text-sky-800">
                Ambulance {dispatchedUnit.callSign} — En Route
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-white rounded-lg p-2 border border-sky-100">
                <div className="text-lg font-black text-sky-700 tabular-nums">
                  {etaCountdown === 0 ? "AT SCENE" : formatCountdown(etaCountdown)}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">ETA</div>
              </div>
              <div className="bg-white rounded-lg p-2 border border-sky-100">
                <div className="text-sm font-extrabold text-slate-900">{dispatchedUnit.distanceKm} km</div>
                <div className="text-xs text-slate-500 mt-0.5">Distance</div>
              </div>
              <div className="bg-white rounded-lg p-2 border border-sky-100">
                <div className="text-sm font-extrabold text-emerald-700">
                  {etaCountdown === 0 ? "On Site" : "Moving"}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">Status</div>
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-sky-800">
              <Navigation className="w-3 h-3" />
              <span>Routing via Emergency Green Corridor → {dispatchedUnit.hospital}</span>
            </div>
          </div>
        )}

        {/* Unit list */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-bold text-slate-700">Available Units:</p>
          {UNITS.map((unit) => {
            const isSelected = selectedUnit === unit.id;
            const isDispatched = unit.id === dispatchedUnitId;
            return (
              <button
                key={unit.id}
                onClick={() => !dispatched && setSelectedUnit(unit.id)}
                disabled={unit.status === "at-scene" || dispatched}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  isDispatched
                    ? "border-sky-400 bg-sky-50"
                    : isSelected && !dispatched
                    ? "border-slate-400 bg-slate-50"
                    : "border-slate-200 bg-white hover:border-slate-300"
                } disabled:opacity-60 disabled:cursor-default`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <Ambulance className="w-3.5 h-3.5 text-sky-600" />
                    <span className="text-xs font-extrabold text-slate-900">Unit {unit.callSign}</span>
                    {isDispatched && <CheckCircle2 className="w-3.5 h-3.5 text-sky-600" />}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${STATUS_COLORS[isDispatched ? "dispatched" : unit.status]}`}>
                    {isDispatched ? "Dispatched" : STATUS_LABELS[unit.status]}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <MapPin className="w-3 h-3" />
                    <span>{unit.location}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    <span>ETA {unit.etaMin} min · {unit.distanceKm} km</span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Dispatch button */}
        {!dispatched && (
          <button
            onClick={() => {
              if (!incidentActive || !selectedUnit) return;
              onDispatch(selectedUnit);
            }}
            disabled={!incidentActive}
            className="w-full py-2.5 bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white text-sm font-extrabold rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all"
          >
            <Ambulance className="w-4 h-4" />
            Dispatch Selected Unit
          </button>
        )}
        {!incidentActive && !dispatched && (
          <p className="text-xs text-center text-slate-400">Simulate an incident first to enable dispatch</p>
        )}
      </div>
    </div>
  );
}
