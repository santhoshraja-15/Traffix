"use client";

import { useEffect, useMemo, useState } from "react";
import { MapPin, X, Check, ShieldAlert, Search } from "lucide-react";
import { loadRealLocations } from "@/services/navigationApi";
import { LocationSuggestion } from "@/types/route";

interface AccidentMapSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRoad: (edgeId: string, roadName: string) => void;
}

export default function AccidentMapSelector({
  isOpen,
  onClose,
  onSelectRoad,
}: AccidentMapSelectorProps) {
  const [locations, setLocations] = useState<LocationSuggestion[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<LocationSuggestion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    loadRealLocations()
      .then(setLocations)
      .catch(() => setError("Anna Nagar location data unavailable."));
  }, [isOpen]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return locations.slice(0, 8);
    return locations.filter((l) => l.name.toLowerCase().includes(q)).slice(0, 8);
  }, [query, locations]);

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
              <p className="text-xs text-slate-500">A real road segment in the loaded Anna Nagar network</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search a real street name..."
            className="w-full pl-8 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-400"
          />
        </div>

        {error && <p className="text-xs text-red-600 font-semibold">{error}</p>}

        {/* Road selection options */}
        <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
          {filtered.length === 0 && !error && (
            <p className="text-xs text-slate-400 text-center py-4">
              {locations.length === 0 ? "Loading real network locations…" : "No matching street found."}
            </p>
          )}
          {filtered.map((loc) => {
            const isChosen = selected?.edge_id === loc.edge_id;
            return (
              <div
                key={loc.edge_id}
                onClick={() => setSelected(loc)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  isChosen
                    ? "bg-red-50/80 border-red-300 shadow-xs"
                    : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <MapPin className={`w-4 h-4 ${isChosen ? "text-red-600" : "text-slate-400"}`} />
                  <span className={`text-xs font-bold ${isChosen ? "text-red-950" : "text-slate-700"}`}>
                    {loc.name}
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
            disabled={!selected}
            onClick={() => {
              if (!selected) return;
              onSelectRoad(selected.edge_id, selected.name);
              onClose();
            }}
            className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:hover:bg-red-600 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Confirm Location</span>
          </button>
        </div>

      </div>
    </div>
  );
}
