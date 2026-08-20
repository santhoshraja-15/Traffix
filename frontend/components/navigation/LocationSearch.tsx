"use client";

import { useState } from "react";
import { Navigation, MapPin, ArrowUpDown, ArrowRight, RefreshCw } from "lucide-react";

interface LocationSearchProps {
  onSearch: (origin: string, destination: string) => void;
  isLoading?: boolean;
}

export default function LocationSearch({
  onSearch,
  isLoading = false,
}: LocationSearchProps) {
  const [origin, setOrigin] = useState("Guindy Junction");
  const [destination, setDestination] = useState("Anna Salai / Gemini Flyover");

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (origin.trim() && destination.trim()) {
      onSearch(origin, destination);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-wrap items-center gap-2"
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
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="Enter starting location..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
          />
        </div>
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
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Enter destination..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all"
          />
        </div>
      </div>

      {/* GO Button */}
      <div className="mt-4">
        <button
          type="submit"
          disabled={isLoading}
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
    </form>
  );
}
