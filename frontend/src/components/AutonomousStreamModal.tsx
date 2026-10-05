"use client";

import React from "react";
import {
  Activity,
  Bot,
  Play,
  Pause,
  RefreshCw,
  Sparkles,
  Send,
  MapPin,
  Instagram,
  CheckCircle2,
  Clock,
  X,
  Zap,
  AlertCircle
} from "lucide-react";
import { AgentStatus } from "@/lib/api";

interface AutonomousStreamModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: AgentStatus | null;
  onToggleAgent: () => void;
  onTriggerHarvest: () => void;
  isHarvesting: boolean;
}

export const AutonomousStreamModal: React.FC<AutonomousStreamModalProps> = ({
  isOpen,
  onClose,
  status,
  onToggleAgent,
  onTriggerHarvest,
  isHarvesting,
}) => {
  if (!isOpen) return null;

  const isActive = status?.is_active ?? false;
  const dispatchedToday = status?.dispatched_today ?? 0;
  const dailyLimit = status?.daily_limit ?? 12;
  const quotaRemaining = status?.available_quota ?? 0;
  const pendingQueue = status?.pending_queue ?? 0;
  const events = status?.recent_events ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-indigo-500/30 bg-slate-950 p-6 shadow-2xl shadow-indigo-500/10">
        {/* Glow accent */}
        <div className="pointer-events-none absolute -top-20 -left-20 h-56 w-56 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -right-20 h-56 w-56 rounded-full bg-emerald-500/10 blur-3xl" />

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/20">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Autonomous AI Agency Agent</h3>
                <span
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isActive ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                    }`}
                  />
                  {status?.status_label || (isActive ? "ACTIVE" : "PAUSED")}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                100% Real Live Engine • APScheduler Daemon • 10-12 Safe DMs/Day Safety Quota
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Telemetry Stat Cards */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Today's Dispatched</span>
              <Send className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-xl font-bold text-white">{dispatchedToday}</span>
              <span className="text-xs text-slate-500">/ {dailyLimit} max</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                style={{ width: `${Math.min(100, (dispatchedToday / dailyLimit) * 100)}%` }}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Remaining Quota</span>
              <Zap className="h-3.5 w-3.5 text-amber-400" />
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-amber-400">{quotaRemaining}</span>
              <span className="text-xs text-slate-500">safe DMs left</span>
            </div>
            <p className="mt-2 text-[10px] text-slate-400">Auto-pauses when 0 to prevent bans</p>
          </div>

          <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Pending Queue</span>
              <Clock className="h-3.5 w-3.5 text-emerald-400" />
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-emerald-400">{pendingQueue}</span>
              <span className="text-xs text-slate-500">intent leads</span>
            </div>
            <p className="mt-2 text-[10px] text-slate-400">Paced 5-12 min randomized</p>
          </div>
        </div>

        {/* Live Controls */}
        <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleAgent}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-bold transition-all shadow-sm active:scale-95 ${
                isActive
                  ? "bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20"
                  : "bg-emerald-600 text-white hover:bg-emerald-500 shadow-emerald-600/20"
              }`}
            >
              {isActive ? (
                <>
                  <Pause className="h-3.5 w-3.5" />
                  <span>Pause Background Agent</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5" />
                  <span>Activate Autonomous Agent</span>
                </>
              )}
            </button>

            <button
              onClick={onTriggerHarvest}
              disabled={isHarvesting}
              className="flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-3.5 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20 active:scale-95 disabled:opacity-50 transition-all"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isHarvesting ? "animate-spin" : ""}`} />
              <span>{isHarvesting ? "Harvesting Live..." : "Harvest Live Intent Now"}</span>
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Activity className="h-3 w-3 text-indigo-400 animate-pulse" />
            <span>Telemetry: Live</span>
          </div>
        </div>

        {/* Real-time Activity Stream */}
        <div className="mt-4">
          <div className="flex items-center justify-between pb-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Live Real-Time Activity Stream
            </h4>
            <span className="text-[11px] text-slate-500">{events.length} recent events</span>
          </div>

          <div className="max-h-60 overflow-y-auto space-y-2 pr-1 rounded-xl border border-slate-800/80 bg-slate-950/80 p-3">
            {events.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                Awaiting next autonomous cycle event...
              </div>
            ) : (
              events.map((evt) => {
                let badgeColor = "bg-slate-800 text-slate-300 border-slate-700";
                let Icon = Activity;

                if (evt.event_type === "dm_sent") {
                  badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
                  Icon = Send;
                } else if (evt.event_type === "harvest") {
                  badgeColor = "bg-purple-500/10 text-purple-400 border-purple-500/30";
                  Icon = Sparkles;
                } else if (evt.event_type === "quota") {
                  badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/30";
                  Icon = AlertCircle;
                } else if (evt.event_type === "maps") {
                  badgeColor = "bg-blue-500/10 text-blue-400 border-blue-500/30";
                  Icon = MapPin;
                }

                return (
                  <div
                    key={evt.id}
                    className="flex items-start gap-2.5 rounded-lg border border-slate-800/50 bg-slate-900/50 p-2 text-xs transition-colors hover:bg-slate-900"
                  >
                    <div className={`mt-0.5 rounded-md p-1 border ${badgeColor}`}>
                      <Icon className="h-3 w-3" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-200 text-xs font-medium leading-relaxed">
                        {evt.message}
                      </p>
                    </div>
                    <span className="whitespace-nowrap font-mono text-[10px] text-slate-500">
                      {evt.timestamp}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
