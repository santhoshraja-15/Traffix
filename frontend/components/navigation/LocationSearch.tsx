"use client";

import { useEffect, useMemo, useState } from "react";
import { Navigation, MapPin, ArrowUpDown, ArrowRight, RefreshCw } from "lucide-react";
import { loadRealLocations } from "@/services/navigationApi";
import { LocationSuggestion } from "@/types/route";

interface LocationSearchProps {
  onSearch: (origin: string, destination: string) => void;
  isLoading?: boolean;
}

function useLocationField(locations: LocationSuggestion[]) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);

  const suggestions = useMemo(() => {
    const q = value.trim().toLowerCase();
    if (!q || locations.length === 0) return [];
    return locations.filter((l) => l.name.toLowerCase().includes(q)).slice(0, 6);
  }, [value, locations]);

  const isValid =
    value.trim().length === 0 ||
    locations.some((l) => l.name.toLowerCase() === value.trim().toLowerCase());

  return { value, setValue, focused, setFocused, suggestions, isValid };
}

export default function LocationSearch({
  onSearch,
  isLoading = false,
}: LocationSearchProps) {
  const [locations, setLocations] = useState<LocationSuggestion[]>([]);
  const [locationsError, setLocationsError] = useState(false);

  useEffect(() => {
    loadRealLocations()
      .then(setLocations)
      .catch(() => setLocationsError(true));
  }, []);

  const origin = useLocationField(locations);
  const destination = useLocationField(locations);

  const handleSwap = () => {
    const temp = origin.value;
    origin.setValue(destination.value);
    destination.setValue(temp);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin.value.trim() || !destination.value.trim()) return;
    if (locations.length > 0 && (!origin.isValid || !destination.isValid)) return;
    onSearch(origin.value.trim(), destination.value.trim());
  };

  const renderSuggestions = (field: ReturnType<typeof useLocationField>) =>
    field.focused && field.suggestions.length > 0 && (
      <ul className="absolute z-30 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden">
        {field.suggestions.map((s) => (
          <li key={s.name}>
            <button
              type="button"
              onMouseDown={(e) => {
                e.preventDefault(); // keep focus so the click registers before blur clears suggestions
                field.setValue(s.name);
              }}
              className="w-full text-left px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-sky-50"
            >
              {s.name}
            </button>
          </li>
        ))}
      </ul>
    );

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-wrap items-start gap-2"
    >
      {/* FROM Input */}
      <div className="flex-1 min-w-[200px] relative">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
          FROM
        </label>
        <div className="relative flex items-center">
          <Navigation className="w-3.5 h-3.5 text-sky-500 absolute left-2.5" />
          <input
            type="text"
            value={origin.value}
            onChange={(e) => origin.setValue(e.target.value)}
            onFocus={() => origin.setFocused(true)}
            onBlur={() => setTimeout(() => origin.setFocused(false), 100)}
            placeholder="e.g. 2nd Avenue"
            className={`w-full pl-8 pr-3 py-1.5 bg-slate-50 border rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all ${
              origin.isValid ? "border-slate-200 focus:border-sky-500" : "border-red-300 focus:border-red-400"
            }`}
          />
        </div>
        {renderSuggestions(origin)}
        {!origin.isValid && (
          <p className="text-[10px] text-red-600 font-semibold mt-0.5">
            Location not found in the supported network
          </p>
        )}
      </div>

      {/* Swap Button (+) */}
      <button
        type="button"
        onClick={handleSwap}
        title="Swap Locations"
        className="mt-4 p-2 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 transition-all active:scale-95"
      >
        <ArrowUpDown className="w-3.5 h-3.5 rotate-90" />
      </button>

      {/* DESTINATION Input */}
      <div className="flex-1 min-w-[200px] relative">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
          DESTINATION
        </label>
        <div className="relative flex items-center">
          <MapPin className="w-3.5 h-3.5 text-red-500 absolute left-2.5" />
          <input
            type="text"
            value={destination.value}
            onChange={(e) => destination.setValue(e.target.value)}
            onFocus={() => destination.setFocused(true)}
            onBlur={() => setTimeout(() => destination.setFocused(false), 100)}
            placeholder="e.g. Anna Nagar Roundabout"
            className={`w-full pl-8 pr-3 py-1.5 bg-slate-50 border rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all ${
              destination.isValid ? "border-slate-200 focus:border-sky-500" : "border-red-300 focus:border-red-400"
            }`}
          />
        </div>
        {renderSuggestions(destination)}
        {!destination.isValid && (
          <p className="text-[10px] text-red-600 font-semibold mt-0.5">
            Location not found in the supported network
          </p>
        )}
      </div>

      {/* GO Button */}
      <div className="mt-4">
        <button
          type="submit"
          disabled={isLoading || locationsError}
          title={locationsError ? "Network location data unavailable" : undefined}
          className="px-5 py-2 bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white text-xs font-bold rounded-lg shadow-sm shadow-sky-200 flex items-center gap-1.5 transition-all disabled:opacity-50"
        >
          {isLoading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <ArrowRight className="w-3.5 h-3.5" />
          )}
          <span>GO</span>
        </button>
      </div>
      {locationsError && (
        <p className="w-full text-[10px] text-red-600 font-semibold">
          Anna Nagar location data unavailable — check the backend connection.
        </p>
      )}
    </form>
  );
}
