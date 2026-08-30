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
import EmergencyStatusPanel from "@/components/emergency/EmergencyStatusPanel";
import LoadingOverlay from "@/components/common/LoadingOverlay";
import WsStatusBadge from "@/components/common/WsStatusBadge";

import { ApplicationMode, IntelligenceMessage } from "@/types/common";
import { RouteOption } from "@/types/route";
import { AccidentSeverity } from "@/types/accident";

import { MOCK_INITIAL_MESSAGES } from "@/lib/mockData";
import { calculateRoutes } from "@/services/navigationApi";
import { simulateAccident, resolveAccident } from "@/services/accidentApi";
import { useLiveKpi, useLiveMessages } from "@/hooks/useLiveData";
import { useTraffixContext } from "@/context/TraffixContext";
import { useRouteReoptimization, RouteUpdateEvent } from "@/hooks/useRouteReoptimization";
import { API_ORIGIN } from "@/lib/constants";
import { CheckCircle2, ShieldAlert, RefreshCw } from "lucide-react";

export default function HomePage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchStepText, setSearchStepText] = useState("");
  const [shortestRouteNotice, setShortestRouteNotice] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [activeSearch, setActiveSearch] = useState<{ origin: string; destination: string } | null>(null);
  const [routeUpdateNotice, setRouteUpdateNotice] = useState<{
    previousEtaMinutes: number;
    nextEtaMinutes: number;
    reason: string;
  } | null>(null);
  const [showComparison, setShowComparison] = useState(false);

  const [mapReady, setMapReady] = useState(false);

  // ── The one app-wide WebSocket connection, owned by TraffixProvider ──────
  const {
    wsConnected,
    wsStep,
    riskByEdge,
    edges,
    vehicles: liveVehicles,
    accidents: liveAccidents,
    missions: liveMissions,
  } = useTraffixContext();
  // Real, backend-confirmed accidents/missions — the UI focuses on the most
  // recent one; the map itself still renders every active one (see TrafficMap).
  const primaryAccident = liveAccidents[0] ?? null;
  const primaryMission = liveMissions[0] ?? null;

  // ── Live KPI + congestion breakdown, computed from the real edge stream ──
  const { kpi } = useLiveKpi(edges);

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
      setRouteUpdateNotice(null);
      setActiveSearch({ origin, destination }); // enables continuous re-evaluation, see below
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
      setActiveSearch(null);
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

  // ── Continuous rerouting: while a route is active, real live risk along
  // its own edges is watched and the backend is asked to re-evaluate only
  // when that signal has moved meaningfully — see hooks/useRouteReoptimization.ts.
  const handleRouteUpdated = ({ previous, result, reason }: RouteUpdateEvent) => {
    setRoutes(result.optimalRoutes);
    setSelectedRoute(result.recommendedRoute);
    setRouteUpdateNotice({
      previousEtaMinutes: previous.etaMinutes,
      nextEtaMinutes: result.recommendedRoute.etaMinutes,
      reason,
    });
    pushMessage({
      id: `msg-${Date.now()}-reroute`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "routing",
      text: "ROUTE UPDATED",
      details: reason,
    });
  };

  useRouteReoptimization({
    active: !!activeSearch && !!selectedRoute,
    origin: activeSearch?.origin ?? "",
    destination: activeSearch?.destination ?? "",
    currentRoute: selectedRoute,
    riskByEdge,
    onRouteUpdated: handleRouteUpdated,
  });

  // Auto-dismiss the ROUTE UPDATED toast after a few seconds, per
  // ANIMATED_EFFECTS.md §3 ("a short ROUTE UPDATED toast/badge").
  useEffect(() => {
    if (!routeUpdateNotice) return;
    const t = setTimeout(() => setRouteUpdateNotice(null), 8000);
    return () => clearTimeout(t);
  }, [routeUpdateNotice]);

  // ── Accident detection — reports a real accident to the backend, which
  // applies a genuine capacity reduction to the affected edge. The resulting
  // rise in real congestion/risk (visible within ~1s on the next simulation
  // tick) is what actually drives everything downstream: road coloring,
  // the KPI panel, and — if the active route uses that edge — a real
  // ROUTE UPDATED via hooks/useRouteReoptimization.ts above. Nothing here
  // fabricates a reroute; the real pipeline does the work.
  const handleSimulateAccident = async (
    edgeId: string,
    roadName: string,
    severity: AccidentSeverity
  ) => {
    try {
      await simulateAccident(edgeId, severity);
      pushMessage({
        id: `msg-${Date.now()}-acc`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "accident",
        text: "⚠ ACCIDENT DETECTED",
        details: `${severity} severity incident on ${roadName}. Backend is recalculating live risk/congestion for the affected road.`,
        urgent: true,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to report the accident.";
      pushMessage({
        id: `msg-${Date.now()}-acc-err`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "warning",
        text: "Accident report failed",
        details: message,
        urgent: true,
      });
    }
  };

  const handleResolveAccident = async (accidentId: string) => {
    try {
      await resolveAccident(accidentId);
      pushMessage({
        id: `msg-${Date.now()}-acc-resolved`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "success",
        text: "Accident resolved",
        details: "The affected road's capacity has been restored.",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to resolve the accident.";
      pushMessage({
        id: `msg-${Date.now()}-acc-resolve-err`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type: "warning",
        text: "Could not resolve accident",
        details: message,
        urgent: true,
      });
    }
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
          activeIncidentsCount={liveAccidents.length}
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

        {/* ROUTE UPDATED — only ever fires from a real backend re-evaluation
            (hooks/useRouteReoptimization.ts), never speculatively */}
        {routeUpdateNotice && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs font-semibold text-emerald-900 flex items-center justify-between shadow-xs animate-pulse">
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                <strong>ROUTE UPDATED</strong> — {Math.round(routeUpdateNotice.previousEtaMinutes)} min →{" "}
                {Math.round(routeUpdateNotice.nextEtaMinutes)} min. {routeUpdateNotice.reason}
              </span>
            </div>
          </div>
        )}

        {/* Route Search Error — real backend/validation failures, never a silent fallback */}
        {searchError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs font-semibold text-red-900 flex items-center gap-2 shadow-xs">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
            <span>{searchError}</span>
          </div>
        )}

        {/* Active Accident Alert Banner — real backend-confirmed accident state */}
        {primaryAccident && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs font-semibold text-red-900 flex items-center justify-between shadow-xs animate-pulse">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span>
                <strong>⚠ ACTIVE INCIDENT:</strong> {primaryAccident.severity} severity on{" "}
                {primaryAccident.road_name || primaryAccident.edge_id}
                {liveAccidents.length > 1 && ` (+${liveAccidents.length - 1} more)`}
              </span>
            </div>
            <button
              onClick={() => handleResolveAccident(primaryAccident.accident_id)}
              className="text-[10px] font-bold bg-red-600 hover:bg-red-700 text-white px-2 py-0.5 rounded uppercase transition-all"
            >
              Clear Accident
            </button>
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
                accidents={liveAccidents}
                missions={liveMissions}
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
              activeAccidentRoadName={primaryAccident?.road_name || primaryAccident?.edge_id}
            />

            <EmergencyStatusPanel mission={primaryMission} />

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
