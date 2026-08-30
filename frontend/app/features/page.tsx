"use client";

import { useState } from "react";
import Link from "next/link";
import Header from "@/components/common/Header";
import {
  ShieldAlert,
  Ambulance,
  Route,
  BarChart3,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from "lucide-react";

interface Capability {
  icon: typeof ShieldAlert;
  title: string;
  status: "real" | "unavailable";
  description: string;
  detail: string;
  linkHref?: string;
  linkLabel?: string;
}

// A real, honest account of what this deployment can and can't do — this
// page used to be a standalone fake demo (hardcoded pre-Phase-3 road IDs,
// a static "Ambulance A-07 / Apollo Hospital Greams Rd" block, fake IoT
// camera devices, fake signal-control toggles). Every one of those either
// duplicated a real workflow that already exists elsewhere in the app, or
// described a capability (traffic-signal control, physical IoT sensors)
// that genuinely doesn't exist in this deployment — see
// app/emergency/mission_manager.py's own signal_priority_available
// disclosure for the same honesty standard applied here.
const CAPABILITIES: Capability[] = [
  {
    icon: Route,
    title: "Dynamic Routing & Risk Scoring",
    status: "real",
    description:
      "Real k-shortest-paths routing over the real Anna Nagar SUMO network (1,234 nodes, 3,187 edges), with live XGBoost V15/V16 congestion and risk scoring refreshed on every request.",
    detail: "app/services/routing_service.py, app/ml/",
    linkHref: "/",
    linkLabel: "Try it on the main map",
  },
  {
    icon: ShieldAlert,
    title: "Accident Simulation & Impact",
    status: "real",
    description:
      "Reporting an accident applies a real capacity reduction to that road's actual graph edge, which genuinely raises congestion/risk on the next tick and can trigger a real reroute for anyone driving through it.",
    detail: "app/services/accident_service.py, app/routing/graph_manager.py",
    linkHref: "/emergency",
    linkLabel: "Open Emergency Command",
  },
  {
    icon: Ambulance,
    title: "Emergency Response Lifecycle",
    status: "real",
    description:
      "An accident automatically dispatches the nearest available real ambulance (seeded from real Anna Nagar hospitals) through a real 7-state mission — dispatch, corridor, en route, arrival, on-site response, return, completion — driven entirely by real simulation ticks.",
    detail: "app/emergency/mission_manager.py, app/emergency/ambulance_manager.py",
    linkHref: "/emergency",
    linkLabel: "Open Emergency Command",
  },
  {
    icon: BarChart3,
    title: "Live Network Analysis",
    status: "real",
    description:
      "Real-time AI insights, per-road live detail, and a live risk-sorted edge table — all derived from the current WebSocket stream, never a canned report.",
    detail: "app/services/analytics_service.py",
    linkHref: "/analysis",
    linkLabel: "Open Analysis & Reasoning",
  },
  {
    icon: ShieldAlert,
    title: "Traffic Signal Control",
    status: "unavailable",
    description:
      "No traffic-light control exists in this deployment — there is no traci.trafficlight.* call anywhere in the codebase. An emergency mission's \"green corridor\" is route-priority only (the ambulance is routed around congestion); it does not actually change any signal.",
    detail: "Disclosed honestly in app/emergency/mission_manager.py (signal_priority_available)",
  },
  {
    icon: ShieldAlert,
    title: "Physical IoT Camera / Sensor Network",
    status: "unavailable",
    description:
      "This deployment has no physical camera or roadside sensor hardware to monitor. All traffic data comes from the SUMO simulation (or real TraCI, when connected) — a monitoring panel for camera devices would have nothing real to show.",
    detail: "No such data source exists anywhere in app/",
  },
];

export default function FeaturesPage() {

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            TRAFFIX Capabilities
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            What this deployment actually does, and what it honestly doesn&apos;t — every real
            feature links to where you can use it live; nothing below is a separate demo with
            its own fake data.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CAPABILITIES.map((cap) => {
            const Icon = cap.icon;
            const isReal = cap.status === "real";
            return (
              <div
                key={cap.title}
                className={`rounded-xl border p-5 shadow-sm flex flex-col gap-3 ${
                  isReal ? "bg-white border-slate-200" : "bg-slate-50 border-slate-200"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center border shrink-0 ${
                        isReal
                          ? "bg-emerald-50 text-emerald-600 border-emerald-100"
                          : "bg-slate-100 text-slate-400 border-slate-200"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="font-extrabold text-slate-900 text-sm">{cap.title}</h3>
                  </div>
                  <span
                    className={`shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                      isReal
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-slate-100 text-slate-500 border-slate-200"
                    }`}
                  >
                    {isReal ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                    {isReal ? "REAL" : "UNAVAILABLE"}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">{cap.description}</p>
                <p className="text-[10px] text-slate-400 font-mono">{cap.detail}</p>

                {cap.linkHref && (
                  <Link
                    href={cap.linkHref}
                    className="mt-auto self-start flex items-center gap-1.5 text-xs font-bold text-sky-600 hover:text-sky-800 transition-all"
                  >
                    {cap.linkLabel}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
