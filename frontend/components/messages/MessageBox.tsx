"use client";

import { IntelligenceMessage } from "../../types/common";
import { Info, AlertTriangle, ShieldAlert, CheckCircle2, Cpu } from "lucide-react";
import { MOCK_INITIAL_MESSAGES } from "../../lib/mockData";

interface MessageBoxProps {
  messages?: IntelligenceMessage[];
}

export default function MessageBox({
  messages = MOCK_INITIAL_MESSAGES,
}: MessageBoxProps) {
  
  const getMessageIcon = (type: string) => {
    switch (type) {
      case "accident":
      case "emergency":
        return <ShieldAlert className="w-3.5 h-3.5 text-red-500 shrink-0" />;
      case "warning":
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />;
      case "success":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />;
      default:
        return <Cpu className="w-3.5 h-3.5 text-sky-500 shrink-0" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-col gap-2 h-[180px]">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
        <h3 className="font-extrabold text-xs tracking-wide text-slate-900 uppercase flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping" />
          LIVE TRAFFIC INTELLIGENCE
        </h3>
        <span className="text-[10px] font-bold text-sky-600 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
          SUMO Feed
        </span>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-1.5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`p-2 rounded-lg text-xs border flex items-start gap-2 transition-all ${
              msg.type === "accident" || msg.type === "emergency"
                ? "bg-red-50/90 border-red-200 text-red-900 font-medium"
                : msg.type === "warning"
                ? "bg-amber-50/90 border-amber-200 text-amber-900"
                : "bg-slate-50 border-slate-200 text-slate-800"
            }`}
          >
            {getMessageIcon(msg.type)}
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[11px]">{msg.text}</span>
                <span className="text-[9px] text-slate-400 font-mono">
                  {msg.timestamp}
                </span>
              </div>
              {msg.details && (
                <p className="text-[10px] opacity-80 mt-0.5 leading-tight">
                  {msg.details}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
