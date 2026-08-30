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
import { useTraffixContext } from "@/context/TraffixContext";
import { API_ORIGIN } from "@/lib/constants";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export default function HomePage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchStepText, setSearchStepText] = useState("");
  const [shortestRouteNotice, setShortestRouteNotice] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [accident, setAccident] = useState<Accident | null>(null);
  const [ambulance, setAmbulance] = useState<Ambulance | null>(null);
  const [showComparison, setShowComparison] = useState(false);

  const [mapReady, setMapReady] = useState(false);

  // ── The one app-wide WebSocket connection, owned by TraffixProvider ──────
  const { wsConnected, wsStep, riskByEdge, edges, vehicles: liveVehicles } = useTraffixContext();

  // ── Live KPI + congestion breakdown, computed from the real edge stream ──
  const { kpi, setKpi } = useLiveKpi(edges);

  // ── Live intelligence message feed ────────────────────────────────────────
  const { messages, pushMessage } = useLiveMessages(MOCK_INITIAL_MESSAGES);

  useEffect(() => {
    if (!mapReady) return;
    fetch(`${API_ORIGIN}/health`)
      .then((res) => res.json())
      .then((data) => {
        console.log("[TRAFFIX] /health", data);
      })
      .catch(() => {
        console.log("[TRAFFIX] /health not reachable yet");
      });
  }, [mapReady]);

  // ── FROM/TO routing — real backend request, no scripted/fake steps ───────
  const handleSearch = async (origin: string, destination: string) => {
    setIsSearching(true);
    setShortestRouteNotice(null);
    setSearchError(null);
    setSearchStepText("Finding shortest route...");

    try {
      const result = await calculateRoutes(origin, destination, riskByEdge);
      setRoutes(result.optimalRoutes);
      setSelectedRoute(result.recommendedRoute);
      setShowComparison(true);
      setShortestRouteNotice(
        `Route found: ${result.recommendedRoute.distanceKm.toFixed(1)} km (~${Math.round(
          result.recommendedRoute.etaMinutes
        )} min)`
      );
      pushMessage({
        id: `msg-${Date.now()}-route`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "success",
        text: "Optimal Route Selected: " + result.recommendedRoute.name,
        details: result.recommendedRoute.reasoning,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Route request failed.";
      setSearchError(message);
      setRoutes([]);
      setSelectedRoute(null);
      setShowComparison(false);
      pushMessage({
        id: `msg-${Date.now()}-err`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "warning",
        text: "Route request failed",
        details: message,
        urgent: true,
      });
    } finally {
      setSearchStepText("");
      setIsSearching(false);
    }
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
      <Header mode={mode} onModeChange={setMode} systemConnected={wsConnected} />

      <main className="flex-1 max-w-[1920px] w-full mx-auto p-4 flex flex-col gap-3 relative">

        {isSearching && (
          <LoadingOverlay
            message="Analyzing Traffic & Optimizing Routes..."
            subtext={searchStepText}
          />
        )}

        {/* WS status bar — reflects the one real app-wide connection */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <WsStatusBadge connected={wsConnected} step={wsStep} />
            {wsConnected && (
              <span className="text-[10px] font-semibold text-slate-400">
                FastAPI simulation stream — map colors throttled to 1s
              </span>
            )}
          </div>
          <span className="text-[10px] font-bold text-slate-400 tabular-nums">
            Sim tick: {wsStep.toLocaleString()}
          </span>
        </div>

        {/* Traffic KPI overview — computed live from the real WebSocket edge stream */}
        <TrafficKpiOverview
          vehicleCount={kpi.activeVehicles}
          averageSpeedKmh={kpi.avgSpeedKmh}
          stoppedVehicles={kpi.stoppedVehicles}
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

        {/* Route Search Error — real backend/validation failures, never a silent fallback */}
        {searchError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs font-semibold text-red-900 flex items-center gap-2 shadow-xs">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
            <span>{searchError}</span>
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
            activeRouteId={selectedRoute?.id}
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
                activeRoute={selectedRoute ?? undefined}
                accident={accident}
                ambulance={ambulance}
                isNavigating={true}
                riskByEdge={riskByEdge}
                vehicles={liveVehicles}
                onBaselineReady={() => setMapReady(true)}
              />
            </div>

            {/* Only shown once a real route exists — "covered so far" is
                honestly 0 (a route was just computed, nothing driven yet);
                there's no active-journey tracking to report otherwise. */}
            {selectedRoute && (
              <JourneyMetrics
                metrics={{
                  distanceCoveredKm: 0,
                  timeTakenMinutes: 0,
                  distanceLeftKm: selectedRoute.distanceKm,
                  timeLeftMinutes: Math.round(selectedRoute.etaMinutes),
                  estimatedReachingTime: new Date(
                    Date.now() + selectedRoute.etaMinutes * 60_000
                  ).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false }),
                  currentSpeedKmh: selectedRoute.averageSpeedKmh,
                }}
              />
            )}
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
              selectedRouteId={selectedRoute?.id}
              onSelectRoute={(r) => setSelectedRoute(r)}
            />

            <CongestionBreakdown
              lowCount={kpi.lowCount}
              moderateCount={kpi.moderateCount}
              highCount={kpi.highCount}
              congestedCount={kpi.congestedCount}
            />

            <LegendPanel />
          </div>

        </div>
      </main>
    </div>
  );
}
