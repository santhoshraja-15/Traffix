"use client";

import { ReactNode } from "react";

// ── Section wrapper ──────────────────────────────────────────────────────────
interface SettingsSectionProps {
  title: string;
  description: string;
  icon: ReactNode;
  children: ReactNode;
  accentColor?: string;
}

export function SettingsSection({
  title,
  description,
  icon,
  children,
  accentColor = "text-sky-600 bg-sky-50 border-sky-100",
}: SettingsSectionProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${accentColor}`}>
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">{title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{description}</p>
        </div>
      </div>
      <div className="divide-y divide-slate-100">{children}</div>
    </div>
  );
}

// ── Row wrapper ──────────────────────────────────────────────────────────────
interface SettingsRowProps {
  label: string;
  description?: string;
  children: ReactNode;
}

export function SettingsRow({ label, description, children }: SettingsRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-slate-800">{label}</p>
        {description && (
          <p className="text-[11px] text-slate-400 mt-0.5">{description}</p>
        )}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

// ── Toggle switch ────────────────────────────────────────────────────────────
interface ToggleProps {
  enabled: boolean;
  onChange: (v: boolean) => void;
  id: string;
}

export function Toggle({ enabled, onChange, id }: ToggleProps) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={enabled}
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none ${
        enabled ? "bg-sky-500" : "bg-slate-200"
      }`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200 ${
          enabled ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

// ── Text input ───────────────────────────────────────────────────────────────
interface TextInputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  id: string;
}

export function TextInput({ value, onChange, placeholder, type = "text", id }: TextInputProps) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-48 sm:w-64 px-3 py-1.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-300 focus:border-sky-400 transition-all placeholder:text-slate-400"
    />
  );
}

// ── Number input ─────────────────────────────────────────────────────────────
interface NumberInputProps {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  id: string;
}

export function NumberInput({ value, onChange, min, max, step = 1, unit, id }: NumberInputProps) {
  return (
    <div className="flex items-center gap-2">
      <input
        id={id}
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-24 px-3 py-1.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-300 focus:border-sky-400 transition-all"
      />
      {unit && <span className="text-xs text-slate-400 font-medium">{unit}</span>}
    </div>
  );
}

// ── Select ───────────────────────────────────────────────────────────────────
interface SelectProps<T extends string> {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string }[];
  id: string;
}

export function Select<T extends string>({ value, onChange, options, id }: SelectProps<T>) {
  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className="px-3 py-1.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-300 focus:border-sky-400 transition-all"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
