"use client";

import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  message?: string;
  subtext?: string;
}

export default function LoadingOverlay({
  message = "Analyzing live traffic...",
  subtext = "Evaluating XGBoost risk probabilities and SUMO road network...",
}: LoadingOverlayProps) {
  return (
    <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-30 flex flex-col items-center justify-center p-6 text-center rounded-xl transition-all">
      <div className="w-12 h-12 rounded-full bg-sky-50 flex items-center justify-center mb-3 border border-sky-100 shadow-sm">
        <Loader2 className="w-6 h-6 text-sky-500 animate-spin" />
      </div>
      <h3 className="font-bold text-slate-800 text-sm tracking-wide">
        {message}
      </h3>
      <p className="text-xs text-slate-500 max-w-sm mt-1">
        {subtext}
      </p>
    </div>
  );
}
