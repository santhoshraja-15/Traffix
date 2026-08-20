export type AlertSeverity = "critical" | "warning" | "info" | "success";

export type AlertCategory =
  | "accident"
  | "emergency"
  | "routing"
  | "signal"
  | "iot"
  | "prediction"
  | "system";

export interface TraffixAlert {
  id: string;
  severity: AlertSeverity;
  category: AlertCategory;
  title: string;
  description: string;
  source: string;
  location?: string;
  timestamp: string;
  acknowledged: boolean;
  dismissed: boolean;
}
