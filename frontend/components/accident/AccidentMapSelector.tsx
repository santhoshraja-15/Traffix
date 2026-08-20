"use client";

import { useState } from "react";
import { MapPin, X, Check, ShieldAlert } from "lucide-react";

interface AccidentMapSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRoad: (roadId: string, roadName: string) => void;
}

const AVAILABLE_ROADS = [
  { id: "road_anna_2", name: "Anna Salai Sec 2 (Teynampet Junction)" },
  { id: "road_anna_3", name: "Anna Salai Sec 3 (Nandanam Crossing)" },
  { id: "road_mount_1", name: "Mount Flyover Bypass (Saidapet)" },
  { id: "road_ring_2", name: "Inner Ring Road (Guindy West)" },
];

export default function AccidentMapSelector({
  isOpen,
  onClose,
  onSelectRoad,
}: AccidentMapSelectorProps) {
  const [selected, setSelected] = useState(AVAILABLE_ROADS[0]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-5 flex flex-col gap-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-red-50 text-red-600 flex items-center justify-center border border-red-100">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-slate-900">
                CHOOSE ACCIDENT LOCATION
              </h3>
              <p className="text-xs text-slate-500">Select target SUMO road segment</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Road selection options */}
        <div className="flex flex-col gap-2">
          {AVAILABLE_ROADS.map((road) => {
            const isChosen = selected.id === road.id;
            return (
              <div
                key={road.id}
                onClick={() => setSelected(road)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  isChosen
                    ? "bg-red-50/80 border-red-300 shadow-xs"
                    : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <MapPin className={`w-4 h-4 ${isChosen ? "text-red-600" : "text-slate-400"}`} />
                  <span className={`text-xs font-bold ${isChosen ? "text-red-950" : "text-slate-700"}`}>
                    {road.name}
                  </span>
                </div>
                {isChosen && <Check className="w-4 h-4 text-red-600 font-bold" />}
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-100 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onSelectRoad(selected.id, selected.name);
              onClose();
            }}
            className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Confirm Location</span>
          </button>
        </div>

      </div>
    </div>
  );
}
