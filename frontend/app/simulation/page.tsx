"use client";

import { useState, useEffect, useRef } from "react";
import Header from "@/components/common/Header";
import { SimulationScenario } from "@/types/simulation";
import SimulationControls from "@/components/simulation/SimulationControls";
import SimulationStatus from "@/components/simulation/SimulationStatus";
import ScenarioSelector from "@/components/simulation/ScenarioSelector";
import AccidentSimulator from "@/components/simulation/AccidentSimulator";
import WsStatusBadge from "@/components/common/WsStatusBadge";
import { useTraffixContext } from "@/context/TraffixContext";
import {
  startSimulation,
  pauseSimulation,
  stopSimulation,
  resetSimulation,
  stepSimulation,
  setSimulationSpeed,
  loadScenario,
} from "@/services/simulationApi";
import { Cpu } from "lucide-react";

export default function SimulationPage() {
  const [scenario, setScenario] = useState<SimulationScenario>("medium");
  const [isRunning, setIsRunning] = useState(true);
  const [speedMultiplier, setSpeedMultiplierState] = useState(1.0);
  const [currentStep, setCurrentStep] = useState(420);
  const [stopped, setStopped] = useState(false);

  // Shared app-wide WS context (single real connection, see TraffixContext.tsx)
  const { wsConnected, wsStep } = useTraffixContext();

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Local tick (UI-driven) — syncs with WS step when connected
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (isRunning && !stopped) {
      intervalRef.current = setInterval(() => {
        setCurrentStep((prev) => prev + 1);
      }, Math.max(100, 1000 / speedMultiplier));
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning, speedMultiplier, stopped]);

  // Sync step from WS when connected
  useEffect(() => {
    if (wsConnected && wsStep > 0) {
      setCurrentStep(wsStep);
    }
  }, [wsStep, wsConnected]);

  // ── API-wired lifecycle handlers ──────────────────────────────────────────
  const handleToggle = async () => {
    if (stopped) return;
    const wasRunning = isRunning;
    setIsRunning(!wasRunning);
    if (wasRunning) {
      await pauseSimulation();
    } else {
      await startSimulation(scenario);
    }
  };

  const handleReset = async () => {
    setStopped(false);
    setIsRunning(true);
    setCurrentStep(0);
    await resetSimulation();
    await startSimulation(scenario);
  };

  const handleStep = async () => {
    if (isRunning || stopped) return;
    const res = await stepSimulation(1);
    if (res.newStep > 0) setCurrentStep(res.newStep);
    else setCurrentStep((prev) => prev + 1);
  };

  const handleStop = async () => {
    setStopped(true);
    setIsRunning(false);
    await stopSimulation();
  };

  const handleSpeedChange = async (v: number) => {
    setSpeedMultiplierState(v);
    await setSimulationSpeed(v);
  };

  const handleScenarioChange = async (s: SimulationScenario) => {
    setScenario(s);
    setCurrentStep(0);
    await loadScenario(s);
    if (isRunning) await startSimulation(s);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Cpu className="w-6 h-6 text-sky-500" />
              SUMO Simulation Command Center
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Control SUMO TraCI lifecycle · Load OSM network scenarios · Monitor real-time network statistics
            </p>
          </div>

          {/* Status badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <WsStatusBadge connected={wsConnected} step={wsStep} />
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-extrabold ${
                stopped
                  ? "bg-slate-100 border-slate-300 text-slate-600"
                  : isRunning
                  ? "bg-emerald-50 border-emerald-300 text-emerald-800"
                  : "bg-amber-50 border-amber-300 text-amber-800"
              }`}
            >
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  stopped
                    ? "bg-slate-400"
                    : isRunning
                    ? "bg-emerald-500 animate-pulse"
                    : "bg-amber-500"
                }`}
              />
              {stopped ? "STOPPED" : isRunning ? "RUNNING" : "PAUSED"}
            </div>
          </div>
        </div>

        {/* Top row: Status + Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SimulationStatus
            isRunning={isRunning && !stopped}
            currentStep={currentStep}
            speedMultiplier={speedMultiplier}
            scenario={scenario}
            traciConnected={wsConnected}
          />
          <SimulationControls
            isRunning={isRunning && !stopped}
            speedMultiplier={speedMultiplier}
            currentStep={currentStep}
            onToggle={handleToggle}
            onReset={handleReset}
            onStep={handleStep}
            onStop={handleStop}
            onSpeedChange={handleSpeedChange}
          />
        </div>

        {/* Bottom row: Scenario Selector + Accident Injector */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ScenarioSelector scenario={scenario} onSelect={handleScenarioChange} />
          <AccidentSimulator
            scenario={scenario}
            isRunning={isRunning && !stopped}
            currentStep={currentStep}
          />
        </div>
      </main>
    </div>
  );
}
