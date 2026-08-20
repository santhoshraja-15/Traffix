"use client";

import { Layers, Eye, EyeOff, Box, Car, TrafficCone, ShieldAlert, Ambulance as AmbulanceIcon, Compass } from "lucide-react";

export interface LayerVisibilityState {
  buildings: boolean;
  vehicles: boolean;
  signals: boolean;
  incidents: boolean;
  emergency: boolean;
  routes: boolean;
}

interface HUDOverlayProps {
  layers: LayerVisibilityState;
  onToggleLayer: (layerKey: keyof LayerVisibilityState) => void;
  onResetCamera?: () => void;
}

export default function HUDOverlay({
  layers,
  onToggleLayer,
  onResetCamera,
}: HUDOverlayProps) {
  return (
    <div className="absolute top-3 right-3 z-20 flex flex-col gap-2 pointer-events-auto">
      
      {/* Layer Visibility Control Box */}
      <div className="bg-slate-900/90 text-white backdrop-blur-md p-2.5 rounded-xl border border-slate-700/60 shadow-lg flex flex-col gap-2 min-w-[170px]">
        <div className="flex items-center justify-between text-[11px] font-bold text-slate-300 border-b border-slate-800 pb-1.5 uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            <span>Map Layers</span>
          </span>
        </div>

        <div className="flex flex-col gap-1 text-xs">
          
          {/* Vehicles Toggle */}
          <button
            onClick={() => onToggleLayer("vehicles")}
            className={`flex items-center justify-between px-2 py-1 rounded-lg transition-all ${
              layers.vehicles ? "bg-sky-500/20 text-sky-300 font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <Car className="w-3.5 h-3.5" />
              <span>Moving Vehicles</span>
            </span>
            {layers.vehicles ? <Eye className="w-3 h-3 text-sky-400" /> : <EyeOff className="w-3 h-3 text-slate-600" />}
          </button>

          {/* 3D Buildings Toggle */}
          <button
            onClick={() => onToggleLayer("buildings")}
            className={`flex items-center justify-between px-2 py-1 rounded-lg transition-all ${
              layers.buildings ? "bg-sky-500/20 text-sky-300 font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <Box className="w-3.5 h-3.5" />
              <span>3D Extrusions</span>
            </span>
            {layers.buildings ? <Eye className="w-3 h-3 text-sky-400" /> : <EyeOff className="w-3 h-3 text-slate-600" />}
          </button>

          {/* Traffic Signals Toggle */}
          <button
            onClick={() => onToggleLayer("signals")}
            className={`flex items-center justify-between px-2 py-1 rounded-lg transition-all ${
              layers.signals ? "bg-sky-500/20 text-sky-300 font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <TrafficCone className="w-3.5 h-3.5" />
              <span>Traffic Signals</span>
            </span>
            {layers.signals ? <Eye className="w-3 h-3 text-sky-400" /> : <EyeOff className="w-3 h-3 text-slate-600" />}
          </button>

          {/* Incidents Toggle */}
          <button
            onClick={() => onToggleLayer("incidents")}
            className={`flex items-center justify-between px-2 py-1 rounded-lg transition-all ${
              layers.incidents ? "bg-red-500/20 text-red-300 font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Accidents & Ripples</span>
            </span>
            {layers.incidents ? <Eye className="w-3 h-3 text-red-400" /> : <EyeOff className="w-3 h-3 text-slate-600" />}
          </button>

          {/* Emergency Corridor Toggle */}
          <button
            onClick={() => onToggleLayer("emergency")}
            className={`flex items-center justify-between px-2 py-1 rounded-lg transition-all ${
              layers.emergency ? "bg-amber-500/20 text-amber-300 font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <AmbulanceIcon className="w-3.5 h-3.5" />
              <span>Ambulance Unit</span>
            </span>
            {layers.emergency ? <Eye className="w-3 h-3 text-amber-400" /> : <EyeOff className="w-3 h-3 text-slate-600" />}
          </button>

        </div>
      </div>

      {/* Camera Reset Button */}
      {onResetCamera && (
        <button
          onClick={onResetCamera}
          className="bg-slate-900/90 text-white hover:bg-slate-800 backdrop-blur-md p-2 rounded-xl border border-slate-700/60 shadow-lg flex items-center justify-center gap-1.5 text-[11px] font-bold transition-all"
        >
          <Compass className="w-3.5 h-3.5 text-sky-400" />
          <span>Reset Camera</span>
        </button>
      )}

    </div>
  );
}
