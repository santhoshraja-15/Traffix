import type { Metadata } from "next";
import "./globals.css";
import { TraffixProvider } from "@/context/TraffixContext";

export const metadata: Metadata = {
  title: "TRAFFIX — Smart Routing Copilot",
  description:
    "Dynamic Traffic Intelligence, XGBoost Risk Prediction, SUMO Digital Twin & Emergency Ambulance Routing.",
  keywords: ["traffic", "routing", "SUMO", "XGBoost", "smart city", "Chennai"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-slate-50 text-slate-900 antialiased flex flex-col min-h-screen">
        <TraffixProvider>{children}</TraffixProvider>
      </body>
    </html>
  );
}
