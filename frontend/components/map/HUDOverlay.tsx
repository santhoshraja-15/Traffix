"use client";

import { Layers, Eye, EyeOff, Box, Car, ShieldAlert, Ambulance as AmbulanceIcon, Compass, Plus, Minus, LocateFixed } from "lucide-react";

export interface LayerVisibilityState {
  buildings: boolean;
  vehicles: boolean;
  incidents: boolean;
  emergency: boolean;
  routes: boolean;
}

interface HUDOverlayProps {
  layers: LayerVisibilityState;
  onToggleLayer: (layerKey: keyof LayerVisibilityState) => void;
  onResetCamera?: () => void;
  /** 3D building extrusion is a real-Mapbox-only concept (fill-extrusion
   * layers need an actual 3D renderer) — this project has never had a real
   * Mapbox token configured, so the flat SVG-fallback map has no 3D
   * buildings to toggle at all. Hide the control there instead of leaving a
   * button that visibly highlights but affects nothing. Defaults to true
   * (shown) so existing callers/tests are unaffected. */
  showBuildingsToggle?: boolean;
  /** Present only in SVG-fallback mode — Mapbox's own zoom controls (when a
   * real token is configured) are unaffected; this map has no scroll-wheel
   * affordance that's discoverable without them. */
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  /** Present only during an active journey once the user has manually
   * panned/zoomed away from the vehicle (see TrafficMap.tsx's autoFollow) —
   * "provide a working recenter/follow vehicle behavior." */
  onRecenterVehicle?: () => void;
}

export default function HUDOverlay({
  layers,
  onToggleLayer,
  onResetCamera,
  showBuildingsToggle = true,
  onZoomIn,
  onZoomOut,
  onRecenterVehicle,
}: HUDOverlayProps) {
  // The map's own drag/zoom listeners are native addEventListener calls on
  // this panel's outer container (see TrafficMap.tsx) — native bubbling
  // reaches that ancestor listener BEFORE React's synthetic event system
  // even runs (React delegates from its own root, which sits above that
  // container), so a React onPointerDown{e => e.stopPropagation()} here
  // cannot stop it. TrafficMap's handler instead checks for this
  // data-map-ui marker directly via e.target.closest(...) and bails out —
  // this attribute is that marker, not decorative.
  return (
    <div
      data-map-ui="true"
      className="absolute top-3 right-3 z-20 flex flex-col gap-2 pointer-events-auto"
    >
      
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

          {/* 3D Buildings Toggle — real-Mapbox-only, see showBuildingsToggle doc above */}
          {showBuildingsToggle && (
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
          )}

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

      {/* Zoom +/- — a discoverable equivalent to wheel/pinch-zoom, which has
          no visible affordance of its own. SVG-fallback mode only; Mapbox
          ships its own zoom control when a real token is configured. */}
      {(onZoomIn || onZoomOut) && (
        <div className="bg-slate-900/90 text-white backdrop-blur-md rounded-xl border border-slate-700/60 shadow-lg flex flex-col overflow-hidden">
          <button
            onClick={onZoomIn}
            disabled={!onZoomIn}
            aria-label="Zoom in"
            className="p-2 hover:bg-slate-800 transition-all flex items-center justify-center border-b border-slate-800 disabled:opacity-40"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onZoomOut}
            disabled={!onZoomOut}
            aria-label="Zoom out"
            className="p-2 hover:bg-slate-800 transition-all flex items-center justify-center disabled:opacity-40"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Recenter on active-journey vehicle — only shown once the user has
          manually panned away from it (see TrafficMap.tsx's autoFollow). */}
      {onRecenterVehicle && (
        <button
          onClick={onRecenterVehicle}
          className="bg-sky-600 text-white hover:bg-sky-700 backdrop-blur-md p-2 rounded-xl border border-sky-400/60 shadow-lg flex items-center justify-center gap-1.5 text-[11px] font-bold transition-all animate-pulse"
        >
          <LocateFixed className="w-3.5 h-3.5" />
          <span>Recenter</span>
        </button>
      )}

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
