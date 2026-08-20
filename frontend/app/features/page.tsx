"use client";

import { useState } from "react";
import Header from "@/components/common/Header";
import { ApplicationMode } from "@/types/common";
import { ShieldAlert, Ambulance as AmbulanceIcon, Route, Play, CheckCircle2 } from "lucide-react";
import { simulateAccident } from "@/services/accidentApi";
import { dispatchAmbulance } from "@/services/ambulanceApi";
import SignalManagementPanel from "@/components/traffic/SignalManagementPanel";
import IotMonitoringPanel from "@/components/traffic/IotMonitoringPanel";

export default function FeaturesPage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [selectedRoad, setSelectedRoad] = useState("road_anna_2");
  const [accidentActive, setAccidentActive] = useState(false);
  const [ambulanceDispatched, setAmbulanceDispatched] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleSimulateAccident = async () => {
    setAccidentActive(true);
    setStatusMessage("⚠ Accident simulated at Anna Salai (Teynampet Junction). Ripple propagation active.");
    await simulateAccident(selectedRoad, "high");
  };

  const handleDispatchAmbulance = async () => {
    setAmbulanceDispatched(true);
    setStatusMessage("🚑 Ambulance A-07 dispatched. Emergency green corridor activated on SUMO network.");
    await dispatchAmbulance("acc-101");
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header mode={mode} onModeChange={setMode} />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            TRAFFIX Features & Intervention Command
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Simulate traffic accidents, trigger emergency ambulance response, monitor IoT cameras/sensors, and test dynamic rerouting on SUMO.
          </p>
        </div>

        {statusMessage && (
          <div className="p-3 bg-sky-50 border border-sky-200 rounded-xl text-sky-800 text-xs font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-sky-600" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Phase 8: Camera & IoT Monitoring Panel */}
        <IotMonitoringPanel />

        {/* Phase 7: Traffic Signal Management Panel */}
        <SignalManagementPanel />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-50 text-red-600 flex items-center justify-center border border-red-100">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm">
                  Accident Simulation
                </h3>
                <p className="text-xs text-slate-500">Inject bottleneck on road</p>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-bold text-slate-700">Target Road Segment:</label>
              <select
                value={selectedRoad}
                onChange={(e) => setSelectedRoad(e.target.value)}
                className="p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800"
              >
                <option value="road_anna_2">Anna Salai Sec 2 (Teynampet)</option>
                <option value="road_mount_1">Mount Flyover Junction</option>
                <option value="road_ring_2">Guindy Inner Ring Road</option>
              </select>
            </div>

            <button
              onClick={handleSimulateAccident}
              className="mt-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-all"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Simulate Accident</span>
            </button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
                <AmbulanceIcon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm">
                  Emergency Response
                </h3>
                <p className="text-xs text-slate-500">Dispatch nearest ambulance</p>
              </div>
            </div>

            <div className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-200">
              <div><strong className="text-slate-900">Nearest Unit:</strong> Ambulance A-07</div>
              <div><strong className="text-slate-900">Hospital:</strong> Apollo Hospital Greams Rd</div>
              <div><strong className="text-slate-900">Est. Dispatch ETA:</strong> 3 minutes</div>
            </div>

            <button
              onClick={handleDispatchAmbulance}
              disabled={!accidentActive}
              className="mt-auto px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white text-xs font-bold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40"
            >
              <AmbulanceIcon className="w-3.5 h-3.5" />
              <span>Assign & Dispatch Unit</span>
            </button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
                <Route className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm">
                  Dynamic Route Scoring
                </h3>
                <p className="text-xs text-slate-500">XGBoost Risk Evaluation</p>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Recalculates route risk exposure at every intersection node in NetworkX graph using live TraCI density metrics.
            </p>

            <div className="mt-auto p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-bold text-emerald-800 text-center">
              Risk Engine Operational
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
