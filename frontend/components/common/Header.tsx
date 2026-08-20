"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ApplicationMode } from "../../types/common";
import { ShieldAlert, BarChart3, Navigation, User, Cpu, Siren, Bell, Settings2 } from "lucide-react";
import { useTraffixContext } from "@/context/TraffixContext";

interface HeaderProps {
  mode: ApplicationMode;
  onModeChange: (newMode: ApplicationMode) => void;
  systemConnected?: boolean;
}

export default function Header({
  mode,
  onModeChange,
  systemConnected = true,
}: HeaderProps) {
  const pathname = usePathname();
  const { unreadAlerts } = useTraffixContext();

  const navItems = [
    { name: "NAVIGATION", path: "/", icon: Navigation, badge: 0 },
    { name: "FEATURES", path: "/features", icon: ShieldAlert, badge: 0 },
    { name: "ANALYSIS & REASONING", path: "/analysis", icon: BarChart3, badge: 0 },
    { name: "SIMULATION", path: "/simulation", icon: Cpu, badge: 0 },
    { name: "EMERGENCY", path: "/emergency", icon: Siren, badge: 0 },
    { name: "ALERTS", path: "/alerts", icon: Bell, badge: unreadAlerts },
    { name: "SETTINGS", path: "/settings", icon: Settings2, badge: 0 },
  ];

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200/80 px-4 py-2.5 shadow-xs sticky top-0 z-50 transition-all">
      <div className="max-w-[1920px] mx-auto flex flex-wrap items-center justify-between gap-4">
        
        {/* Brand & Tagline */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center text-white font-extrabold text-xl shadow-md shadow-sky-500/20 group-hover:scale-105 transition-all">
            T
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-xl tracking-tight text-slate-900 group-hover:text-sky-600 transition-colors">
                TRAFFIX
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-sky-50 text-sky-700 border border-sky-200">
                v15.0
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium tracking-wide">
              Smart Routing Copilot!
            </p>
          </div>
        </Link>

        {/* Mode Selector & Status */}
        <div className="flex items-center gap-4">
          
          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-100/80 p-1 rounded-xl border border-slate-200 text-xs font-semibold">
            <span className="text-slate-500 px-2 text-[11px] uppercase tracking-wider font-extrabold hidden sm:inline">
              MODE:
            </span>
            <button
              onClick={() => onModeChange("simulation")}
              className={`px-3 py-1 rounded-lg transition-all ${
                mode === "simulation"
                  ? "bg-white text-sky-600 shadow-xs font-extrabold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              SIMULATION
            </button>
            <button
              onClick={() => onModeChange("realtime")}
              className={`px-3 py-1 rounded-lg transition-all ${
                mode === "realtime"
                  ? "bg-white text-emerald-600 shadow-xs font-extrabold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              REALTIME
            </button>
          </div>

          {/* Connection Status Badge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full text-xs bg-slate-50 border border-slate-200">
            <span
              className={`w-2 h-2 rounded-full ${
                systemConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
              }`}
            />
            <span className="text-slate-600 font-semibold">
              {systemConnected ? "SUMO Stream Active" : "Local Mock Engine"}
            </span>
          </div>

        </div>

        {/* Right Navigation Controls */}
        <div className="flex items-center gap-2">
          <nav className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-extrabold transition-all ${
                    isActive
                      ? "bg-sky-50 text-sky-600 border border-sky-200/80 shadow-2xs"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden lg:inline">{item.name}</span>
                  {item.badge > 0 && (
                    <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-4 h-4 px-1 bg-red-500 text-white text-[9px] font-black rounded-full animate-pulse shadow-xs">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User Button */}
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100/90 text-slate-700 hover:bg-slate-200 text-xs font-extrabold border border-slate-200 transition-all">
            <User className="w-3.5 h-3.5 text-slate-600" />
            <span className="hidden sm:inline">USER</span>
          </button>
        </div>

      </div>
    </header>
  );
}
