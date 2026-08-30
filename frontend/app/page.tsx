"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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

import { RouteOption } from "@/types/route";
import { AccidentSeverity } from "@/types/accident";

import { buildTurnInstructions } from "@/lib/turnInstructions";
import { calculateRoutes } from "@/services/navigationApi";
import { simulateAccident, resolveAccident } from "@/services/accidentApi";
import { useLiveKpi } from "@/hooks/useLiveData";
import { useTraffixContext } from "@/context/TraffixContext";
import {
  useRouteReoptimization,
  RouteUpdateEvent,
  EmergencyZoneWarningEvent,
} from "@/hooks/useRouteReoptimization";
import { API_ORIGIN } from "@/lib/constants";
import { fetchHealth } from "@/services/networkApi";
import { CheckCircle2, ShieldAlert, RefreshCw } from "lucide-react";

export default function HomePage() {
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
    isEmergencyZone: boolean;
  } | null>(null);
  // A real, currently-active accident sits on the user's active route, but
  // the backend genuinely found nothing faster than the ETA already
  // promised (an accident only ever makes the area worse) — honest warning,
  // never a fabricated "we rerouted you" claim. See useRouteReoptimization's
  // EmergencyZoneWarningEvent doc comment.
  const [zoneWarning, setZoneWarning] = useState<{ severity: string; roadName: string } | null>(null);

  // ── Journey progress — real elapsed time only, never a fabricated
  // position/distance (see JourneyMetrics.tsx's doc comment: no backend
  // capability exists to track an ordinary user's live position along a
  // route, unlike SUMO vehicles or the emergency-mission system). ─────────
  const [journeyStartedAt, setJourneyStartedAt] = useState<number | null>(null);
  const [journeyNow, setJourneyNow] = useState<number | null>(null);
  const lastJourneyRouteId = useRef<string | undefined>(undefined);
  const [showComparison, setShowComparison] = useState(false);

  const [mapReady, setMapReady] = useState(false);

  // ── The one app-wide WebSocket connection, owned by TraffixProvider ──────
  const {
    wsConnected,
    wsStep,
    dataSource,
    riskByEdge,
    edges,
    vehicles: liveVehicles,
    accidents: liveAccidents,
    missions: liveMissions,
    messages,
    pushMessage,
  } = useTraffixContext();
  // Real, backend-confirmed accidents/missions — the UI focuses on the most
  // recent one; the map itself still renders every active one (see TrafficMap).
  const primaryAccident = liveAccidents[0] ?? null;
  const primaryMission = liveMissions[0] ?? null;

  // Real "next instruction" — derived entirely from the active route's own
  // geometry and real ordered street names (lib/turnInstructions.ts). There
  // is no live GPS feed for the person planning a route here, so this is
  // the route's first real maneuver from its start, not a live position
  // update — never the fabricated "Turn right onto Anna Salai Direct"
  // default NavigationBar used to render unconditionally.
  const nextInstruction = useMemo(() => {
    if (!selectedRoute) return undefined;
    const steps = buildTurnInstructions(selectedRoute.coordinates, selectedRoute.roadNames);
    const first = steps[0];
    if (!first) return undefined;
    return {
      ...first,
      timeSeconds:
        selectedRoute.averageSpeedKmh > 0
          ? Math.round((first.distanceMeters / 1000 / selectedRoute.averageSpeedKmh) * 3600)
          : 0,
    };
  }, [selectedRoute]);

  // ── Live KPI + congestion breakdown, computed from the real edge stream ──
  const { kpi } = useLiveKpi(edges);

  // Real "rescue success" notice — fires once per mission, exactly when its
  // real state actually transitions to emergency_completed (never guessed,
  // never re-fired on every render while it stays completed).
  const seenCompletedMissions = useRef<Set<string>>(new Set());
  useEffect(() => {
    for (const m of liveMissions) {
      if (m.state === "emergency_completed" && !seenCompletedMissions.current.has(m.mission_id)) {
        seenCompletedMissions.current.add(m.mission_id);
        pushMessage({
          id: `msg-${Date.now()}-rescue-${m.mission_id}`,
          timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
          type: "success",
          text: "✅ Rescue completed",
          details: `${m.unit_number} completed the mission from ${m.hospital_name} and returned to service.`,
        });
      }
    }
  }, [liveMissions, pushMessage]);

  useEffect(() => {
    if (!mapReady) return;
    // Timeout-protected (see services/networkApi.ts::fetchHealth) — this
    // used to be its own raw fetch() with no bound, duplicating
    // fetchHealth() while also lacking its timeout fix.
    fetchHealth()
      .then((data) => {
        console.log("[TRAFFIX] /health", data);
        pushMessage({
          id: `msg-${Date.now()}-health`,
          timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
          type: "info",
          text: "Backend Connected",
          details: `TRAFFIX API v${data.version ?? "?"} reachable at ${API_ORIGIN}.`,
        });
      })
      .catch(() => {
        console.log("[TRAFFIX] /health not reachable yet");
        pushMessage({
          id: `msg-${Date.now()}-health-err`,
          timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
          type: "warning",
          text: "Backend Offline",
          details: `Could not reach ${API_ORIGIN}/health.`,
          urgent: true,
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapReady]);

  // ── Real system-level connect/disconnect notice — pushed only on an
  // actual state transition (never spammy re-pushes while steady), using
  // the same wsConnected flag the status badge already reflects.
  const prevWsConnected = useRef<boolean | null>(null);
  useEffect(() => {
    if (prevWsConnected.current === null) {
      prevWsConnected.current = wsConnected;
      return;
    }
    if (prevWsConnected.current === wsConnected) return;
    prevWsConnected.current = wsConnected;
    pushMessage({
      id: `msg-${Date.now()}-ws`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "system",
      text: wsConnected ? "Realtime stream connected" : "Realtime stream disconnected",
      details: wsConnected
        ? "Live simulation WebSocket reconnected — map and KPIs resuming."
        : "Live simulation WebSocket dropped — attempting to reconnect.",
      urgent: !wsConnected,
    });
  }, [wsConnected, pushMessage]);

  // Selecting a different route (a new search, or picking an alternate from
  // TopRoutes/RouteComparison) ends any in-progress journey — starting a
  // journey is a real, deliberate action tied to a specific route, not
  // something that should silently carry over to a route the user never
  // clicked "Start Journey" on.
  useEffect(() => {
    if (selectedRoute?.id !== lastJourneyRouteId.current) {
      lastJourneyRouteId.current = selectedRoute?.id;
      setJourneyStartedAt(null);
    }
  }, [selectedRoute?.id]);

  // Real wall-clock ticking, once per second, only while a journey is
  // actually in progress — this is the one genuinely live figure
  // JourneyMetrics shows (Time Elapsed); everything else on that panel is
  // either the route's real planned totals or honestly "not tracked."
  useEffect(() => {
    if (journeyStartedAt === null) {
      setJourneyNow(null);
      return;
    }
    setJourneyNow(Date.now());
    const interval = setInterval(() => setJourneyNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [journeyStartedAt]);

  const elapsedMinutes =
    journeyStartedAt !== null && journeyNow !== null ? (journeyNow - journeyStartedAt) / 60_000 : null;

  const handleStartJourney = () => {
    if (!selectedRoute) return;
    setJourneyStartedAt(Date.now());
    pushMessage({
      id: `msg-${Date.now()}-journey-start`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "system",
      text: "Navigation started",
      details: `Journey started on ${selectedRoute.name}. Elapsed time is real; distance covered has no live position feed to track.`,
    });
  };

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
  const handleRouteUpdated = ({ previous, result, reason, isEmergencyZone }: RouteUpdateEvent) => {
    setRoutes(result.optimalRoutes);
    setSelectedRoute(result.recommendedRoute);
    setRouteUpdateNotice({
      previousEtaMinutes: previous.etaMinutes,
      nextEtaMinutes: result.recommendedRoute.etaMinutes,
      reason,
      isEmergencyZone,
    });
    pushMessage({
      id: `msg-${Date.now()}-reroute`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: isEmergencyZone ? "emergency" : "routing",
      text: isEmergencyZone ? "⚠ EMERGENCY ZONE AHEAD" : "ROUTE UPDATED",
      details: reason,
      urgent: isEmergencyZone,
    });
  };

  const handleEmergencyZoneWarning = ({ accident }: EmergencyZoneWarningEvent) => {
    setZoneWarning({ severity: accident.severity, roadName: accident.road_name });
    pushMessage({
      id: `msg-${Date.now()}-zone-warning`,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      type: "emergency",
      text: "⚠ ACTIVE ACCIDENT ON YOUR ROUTE",
      details: `${accident.road_name} — ${accident.severity.toUpperCase()} severity. No faster alternative was found; continue with caution.`,
      urgent: true,
    });
  };

  useRouteReoptimization({
    active: !!activeSearch && !!selectedRoute,
    origin: activeSearch?.origin ?? "",
    destination: activeSearch?.destination ?? "",
    currentRoute: selectedRoute,
    riskByEdge,
    accidents: liveAccidents,
    onRouteUpdated: handleRouteUpdated,
    onEmergencyZoneWarning: handleEmergencyZoneWarning,
  });

  // Auto-dismiss the ROUTE UPDATED toast after a few seconds, per
  // ANIMATED_EFFECTS.md §3 ("a short ROUTE UPDATED toast/badge").
  useEffect(() => {
    if (!routeUpdateNotice) return;
    const t = setTimeout(() => setRouteUpdateNotice(null), 8000);
    return () => clearTimeout(t);
  }, [routeUpdateNotice]);

  useEffect(() => {
    if (!zoneWarning) return;
    const t = setTimeout(() => setZoneWarning(null), 8000);
    return () => clearTimeout(t);
  }, [zoneWarning]);

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
      <Header />

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
            <WsStatusBadge connected={wsConnected} step={wsStep} mock={dataSource === "mock"} />
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

        {/* ROUTE UPDATED / EMERGENCY ZONE AHEAD — only ever fires from a real
            backend re-evaluation (hooks/useRouteReoptimization.ts), never
            speculatively. One coherent banner per ANIMATED_EFFECTS.md §8,
            styled distinctly (emergency palette) when the trigger was a
            real accident on the active route. */}
        {routeUpdateNotice && (
          <div
            className={`rounded-xl p-3 text-xs font-semibold flex items-center justify-between shadow-xs animate-pulse ${
              routeUpdateNotice.isEmergencyZone
                ? "bg-red-50 border border-red-300 text-red-900"
                : "bg-emerald-50 border border-emerald-200 text-emerald-900"
            }`}
          >
            <div className="flex items-center gap-2">
              {routeUpdateNotice.isEmergencyZone ? (
                <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
              ) : (
                <RefreshCw className="w-4 h-4 text-emerald-600 shrink-0" />
              )}
              <span>
                <strong>{routeUpdateNotice.isEmergencyZone ? "EMERGENCY ZONE AHEAD" : "ROUTE UPDATED"}</strong> —{" "}
                {Math.round(routeUpdateNotice.previousEtaMinutes)} min →{" "}
                {Math.round(routeUpdateNotice.nextEtaMinutes)} min. {routeUpdateNotice.reason}
              </span>
            </div>
          </div>
        )}

        {/* ACTIVE ACCIDENT ON YOUR ROUTE — a real accident sits on the active
            route but the backend found nothing genuinely faster than the ETA
            already promised (an accident only ever makes the area worse, so
            that bar often can't be cleared). Honest hazard warning, never a
            fabricated "rerouted" claim — see EmergencyZoneWarningEvent. */}
        {zoneWarning && (
          <div className="rounded-xl p-3 text-xs font-semibold flex items-center justify-between shadow-xs animate-pulse bg-red-50 border border-red-300 text-red-900">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
              <span>
                <strong>ACTIVE ACCIDENT ON YOUR ROUTE</strong> — {zoneWarning.roadName} (
                {zoneWarning.severity.toUpperCase()}). No faster alternative was found; continue with caution.
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
            <NavigationBar areaName="Anna Nagar, Chennai" instruction={nextInstruction} />

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

            {/* Only shown once a real route exists. Time Elapsed is real
                (wall-clock since Start Journey); Distance Covered is
                honestly "not tracked" — see JourneyMetrics.tsx's doc
                comment for why neither can be faked here. */}
            {selectedRoute && (
              <JourneyMetrics
                route={selectedRoute}
                journeyStartedAt={journeyStartedAt}
                elapsedMinutes={elapsedMinutes}
                onStartJourney={handleStartJourney}
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
