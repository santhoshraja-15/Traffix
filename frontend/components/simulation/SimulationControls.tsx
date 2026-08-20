"use client";

import { Play, Pause, RotateCcw, SkipForward, Square } from "lucide-react";

interface SimulationControlsProps {
  isRunning: boolean;
  speedMultiplier: number;
  currentStep: number;
  onToggle: () => void;
  onReset: () => void;
  onStep: () => void;
  onStop: () => void;
  onSpeedChange: (v: number) => void;
}

const SPEED_MARKS = [0.5, 1.0, 2.0, 3.0, 5.0];

export default function SimulationControls({
  isRunning,
  speedMultiplier,
  currentStep,
  onToggle,
  onReset,
  onStep,
  onStop,
  onSpeedChange,
}: SimulationControlsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Simulation Lifecycle Controls</h3>
          <p className="text-xs text-slate-500 mt-0.5">SUMO TraCI step engine — Anna Salai OSM Network</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg tabular-nums">
          Step&nbsp;<span className="text-slate-900">{currentStep.toLocaleString()}</span>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-5">
        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={onToggle}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-extrabold text-white shadow-sm transition-all ${
              isRunning
                ? "bg-amber-500 hover:bg-amber-600"
                : "bg-emerald-600 hover:bg-emerald-700"
            }`}
          >
            {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isRunning ? "Pause" : "Resume"}
          </button>

          <button
            onClick={onStep}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all disabled:opacity-40"
          >
            <SkipForward className="w-4 h-4" />
            Step +1
          </button>

          <button
            onClick={onReset}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>

          <button
            onClick={onStop}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition-all"
          >
            <Square className="w-4 h-4" />
            Stop
          </button>
        </div>

        {/* Speed slider */}
        <div className="flex flex-col gap-2.5">
          <div className="flex justify-between items-center">
            <span className="text-xs font-bold text-slate-700">Simulation Speed</span>
            <span className="text-xs font-extrabold text-sky-600 bg-sky-50 border border-sky-100 px-2 py-0.5 rounded-lg">
              {speedMultiplier.toFixed(1)}×
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="5.0"
            step="0.5"
            value={speedMultiplier}
            onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-100 rounded-full appearance-none cursor-pointer accent-sky-500"
          />
          <div className="flex justify-between text-[10px] text-slate-400 font-semibold">
            {SPEED_MARKS.map((m) => (
              <span key={m}>{m}×</span>
            ))}
          </div>
        </div>

        {/* Step progress */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-700">Simulation Progress</span>
            <span className="text-slate-400">{Math.round((currentStep / 3600) * 100)}% of 1hr epoch</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-gradient-to-r from-sky-400 to-sky-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (currentStep / 3600) * 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
