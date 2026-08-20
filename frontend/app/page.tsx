"use client";

import { useEffect, useState } from "react";
import Header from "@/components/common/Header";
import LocationSearch from "@/components/navigation/LocationSearch";
import NavigationBar from "@/components/navigation/NavigationBar";
import TrafficMap from "@/components/map/TrafficMap";
import JourneyMetrics from "@/components/navigation/JourneyMetrics";
import MessageBox from "@/components/messages/MessageBox";
import TopRoutes from "@/components/routes/TopRoutes";
import RouteComparison from "@/components/routes/RouteComparison";
import LegendPanel from "@/components/map/LegendPanel";
import TrafficKpiOverview from "@/components/traffic/TrafficKpiOverview";
import CongestionBreakdown from "@/components/traffic/CongestionBreakdown";
import AccidentPanel from "@/components/accident/AccidentPanel";
import LoadingOverlay from "@/components/common/LoadingOverlay";
import WsStatusBadge from "@/components/common/WsStatusBadge";

import { ApplicationMode, IntelligenceMessage } from "@/types/common";
import { RouteOption } from "@/types/route";
import { Accident, AccidentSeverity } from "@/types/accident";
import { Ambulance } from "@/types/ambulance";

import { MOCK_ROUTES, MOCK_INITIAL_MESSAGES } from "@/lib/mockData";
import { calculateRoutes } from "@/services/navigationApi";
import { simulateAccident } from "@/services/accidentApi";
import { useLiveKpi, useLiveMessages } from "@/hooks/useLiveData";
import { useSimulationStream } from "@/hooks/useSimulationStream";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export default function HomePage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [routes, setRoutes] = useState<RouteOption[]>(MOCK_ROUTES);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption>(MOCK_ROUTES[0]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchStepText, setSearchStepText] = useState("");
  const [shortestRouteNotice, setShortestRouteNotice] = useState<string | null>(null);
  const [accident, setAccident] = useState<Accident | null>(null);
  const [ambulance, setAmbulance] = useState<Ambulance | null>(null);
  const [showComparison, setShowComparison] = useState(false);

  const [mapReady, setMapReady] = useState(false);

  // ── Phase 15: Live KPI from WebSocket + REST polling ────────────────────
  const { kpi, wsConnected, wsStep, isMockFeed, setKpi } = useLiveKpi(5000, mapReady);

  // ── Phase 2: FastAPI simulation stream (starts only after baseline map) ─
  const { connected: simConnected, riskByEdge, tick: simTick } = useSimulationStream(mapReady);

  // ── Phase 15: Live intelligence message feed ─────────────────────────────
  const { messages, pushMessage } = useLiveMessages(MOCK_INITIAL_MESSAGES);

  useEffect(() => {
    if (!mapReady) return;
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => {
        console.log("[TRAFFIX] /health", data);
      })
      .catch(() => {
        console.log("[TRAFFIX] /health not reachable yet");
      });
  }, [mapReady]);

  // ── Phase 4: Route Optimization Workflow ─────────────────────────────────
  const handleSearch = async (origin: string, destination: string) => {
    setIsSearching(true);
    setShortestRouteNotice(null);

    setSearchStepText("Step 1/3: Mapping locations to SUMO network nodes...");
    pushMessage({
      id: `msg-${Date.now()}-1`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "info",
      text: `Resolving locations: ${origin} → ${destination}`,
      details: "Mapping geographic coordinates to SUMO edge IDs...",
    });

    setTimeout(() => {
      setSearchStepText("Step 2/3: Shortest topological path found...");
      setShortestRouteNotice("Shortest topological route found: 4.2 km (~12 min)");
      pushMessage({
        id: `msg-${Date.now()}-2`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "routing",
        text: "Shortest Route Found",
        details: "Topological shortest path calculated via Anna Salai Direct.",
      });
    }, 600);

    setTimeout(() => {
      setSearchStepText("Step 3/3: Evaluating XGBoost risk & live TraCI traffic...");
      pushMessage({
        id: `msg-${Date.now()}-3`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "system",
        text: "Analyzing Live Traffic & XGBoost Risk...",
        details: "Evaluating congestion, speed vectors, and risk exposure scores.",
      });
    }, 1200);

    setTimeout(async () => {
      const result = await calculateRoutes(origin, destination);
      setRoutes(result.optimalRoutes);
      setSelectedRoute(result.recommendedRoute);
      setShowComparison(true);

      pushMessage({
        id: `msg-${Date.now()}-4`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "success",
        text: "Optimal Route Selected: " + result.recommendedRoute.name,
        details: result.recommendedRoute.reasoning,
      });
      setIsSearching(false);
    }, 1800);
  };

  // ── Phase 5: Accident Simulation & Dynamic Rerouting ─────────────────────
  const handleSimulateAccident = async (
    roadId: string,
    roadName: string,
    severity: AccidentSeverity
  ) => {
    const newAccident = await simulateAccident(roadId, severity);
    setAccident(newAccident);

    // Degrade KPI live
    setKpi((prev) => ({
      ...prev,
      activeIncidents: prev.activeIncidents + 1,
      networkHealthPct: Math.max(40, prev.networkHealthPct - 24),
      congestionIndex: Math.min(1, prev.congestionIndex + 0.2),
    }));

    pushMessage({
      id: `msg-${Date.now()}-acc`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "accident",
      text: "⚠ ACCIDENT DETECTED",
      details: `Major bottleneck on ${roadName}. Route blocked. Recalculating alternatives...`,
      urgent: true,
    });

    setTimeout(() => {
      const reroutedRoutes: RouteOption[] = [
        { ...MOCK_ROUTES[1], isRecommended: true, reasoning: "Bypasses severe accident at Teynampet Junction via Mount Flyover." },
        { ...MOCK_ROUTES[2], isRecommended: false },
        { ...MOCK_ROUTES[0], congestion: "congested", riskScore: 0.95, score: 12.0, isRecommended: false, reasoning: "BLOCKED by active multi-vehicle accident." },
      ];
      setRoutes(reroutedRoutes);
      setSelectedRoute(reroutedRoutes[0]);

      pushMessage({
        id: `msg-${Date.now()}-reroute`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "routing",
        text: "Traffic Rerouted: Mount Flyover Bypass Selected",
        details: "Navigation automatically updated to avoid high-risk bottleneck.",
      });
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header mode={mode} onModeChange={setMode} systemConnected={simConnected || wsConnected} />

      <main className="flex-1 max-w-[1920px] w-full mx-auto p-4 flex flex-col gap-3 relative">

        {isSearching && (
          <LoadingOverlay
            message="Analyzing Traffic & Optimizing Routes..."
            subtext={searchStepText}
          />
        )}

        {/* Phase 15: WS status bar */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <WsStatusBadge
              connected={simConnected || wsConnected}
              mock={isMockFeed && !simConnected}
              step={simTick ?? wsStep}
            />
            {simConnected && (
              <span className="text-[10px] font-semibold text-slate-400">
                FastAPI simulation stream — map colors throttled to 1s
              </span>
            )}
          </div>
          {simTick !== undefined && (
            <span className="text-[10px] font-bold text-slate-400 tabular-nums">
              Sim tick: {simTick.toLocaleString()}
            </span>
          )}
        </div>

        {/* Phase 2: Traffic KPI — now driven by live useLiveKpi */}
        <TrafficKpiOverview
          vehicleCount={kpi.activeVehicles}
          averageSpeedKmh={kpi.avgSpeedKmh}
          stoppedVehicles={accident ? 28 : 12}
          networkHealthIndex={kpi.networkHealthPct}
          activeIncidentsCount={kpi.activeIncidents}
        />

        {/* Search Card */}
        <LocationSearch onSearch={handleSearch} isLoading={isSearching} />

        {/* Shortest Route Notice */}
        {shortestRouteNotice && (
          <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 text-xs font-semibold text-sky-900 flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-sky-600" />
              <span>{shortestRouteNotice}</span>
            </div>
            <span className="text-[10px] font-bold bg-sky-200/60 text-sky-800 px-2 py-0.5 rounded">
              Route Optimization Active
            </span>
          </div>
        )}

        {/* Active Accident Alert Banner */}
        {accident && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs font-semibold text-red-900 flex items-center justify-between shadow-xs animate-pulse">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span>
                <strong>⚠ ACTIVE INCIDENT:</strong> {accident.description} on {accident.roadName}
              </span>
            </div>
            <span className="text-[10px] font-bold bg-red-600 text-white px-2 py-0.5 rounded uppercase">
              Corridor Blocked
            </span>
          </div>
        )}

        {/* Route Comparison Drawer */}
        {showComparison && (
          <RouteComparison
            routes={routes}
            activeRouteId={selectedRoute.id}
            onSelectRoute={(r) => setSelectedRoute(r)}
          />
        )}

        {/* Main Workspace Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start flex-1">

          {/* LEFT: Map View & Journey Metrics */}
          <div className="lg:col-span-8 flex flex-col gap-2 h-full">
            <NavigationBar areaName="Anna Nagar, Chennai" />

            <div className="h-[520px] w-full relative shadow-sm rounded-b-xl">
              <TrafficMap
                activeRoute={selectedRoute}
                accident={accident}
                ambulance={ambulance}
                isNavigating={true}
                riskByEdge={riskByEdge}
                onBaselineReady={() => setMapReady(true)}
              />
            </div>

            <JourneyMetrics
              metrics={{
                distanceCoveredKm: 1.4,
                timeTakenMinutes: 4,
                distanceLeftKm: Math.max(0, selectedRoute.distanceKm - 1.4),
                timeLeftMinutes: Math.max(0, selectedRoute.etaMinutes - 4),
                estimatedReachingTime: "17:05",
                currentSpeedKmh: selectedRoute.averageSpeedKmh,
              }}
            />
          </div>

          {/* RIGHT: Live Messages, Accident Panel, Routes, Congestion, Legend */}
          <div className="lg:col-span-4 flex flex-col gap-3">
            {/* Phase 15: MessageBox now driven by live useLiveMessages */}
            <MessageBox messages={messages} />

            <AccidentPanel
              onSimulateAccident={handleSimulateAccident}
              activeAccidentRoadName={accident?.roadName}
            />

            <TopRoutes
              routes={routes}
              selectedRouteId={selectedRoute.id}
              onSelectRoute={(r) => setSelectedRoute(r)}
            />

            <CongestionBreakdown
              lowCount={accident ? 20 : 26}
              moderateCount={8}
              highCount={accident ? 7 : 3}
              congestedCount={accident ? 3 : 1}
            />

            <LegendPanel />
          </div>

        </div>
      </main>
    </div>
  );
}
