"use client";

import React from "react";
import {
  Sparkles,
  Database,
  ExternalLink,
  RefreshCw,
  Target,
  Instagram,
  MapPin,
  Send,
  Loader2,
  Layers,
  Bot,
  Activity
} from "lucide-react";
import { AgentStatus } from "@/lib/api";

interface HeaderProps {
  isBackendConnected: boolean;
  isSeeding: boolean;
  onSeedData: () => void;
  onRefresh: () => void;
  onOpenTargetNiche?: () => void;
  onOpenScanInstagram?: () => void;
  onOpenScanMaps?: () => void;
  dailyIgLimit?: number;
  onDailyIgLimitChange?: (limit: number) => void;
  onDispatchIgBatch?: () => void;
  isDispatchingIg?: boolean;
  igQueueCount?: number;
  igSentToday?: number;
  agentStatus?: AgentStatus | null;
  onOpenAgentStream?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isBackendConnected,
  isSeeding,
  onSeedData,
  onRefresh,
  onOpenTargetNiche,
  onOpenScanInstagram,
  onOpenScanMaps,
  dailyIgLimit = 15,
  onDailyIgLimitChange,
  onDispatchIgBatch,
  isDispatchingIg = false,
  igQueueCount = 0,
  igSentToday = 0,
  agentStatus,
  onOpenAgentStream,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand & Stage Badge */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Sparkles className="h-5 w-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                ApexLead{" "}
                <span className="bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">
                  AI
                </span>
              </h1>
              <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[11px] font-bold text-indigo-300">
                Autonomous Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Live Google Maps Scraping • Real IG Intent • Automated Outreach
            </p>
          </div>
        </div>

        {/* Right Actions & Automation Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Live Autonomous Agent Status Indicator */}
          {agentStatus && (
            <button
              onClick={onOpenAgentStream}
              title="Click to view real-time autonomous telemetry & controls"
              className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-bold transition-all shadow-sm active:scale-95 ${
                agentStatus.is_active
                  ? "border-emerald-500/40 bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/40 hover:border-emerald-500/70"
                  : "border-amber-500/40 bg-amber-950/40 text-amber-300 hover:bg-amber-900/40 hover:border-amber-500/70"
              }`}
            >
              <span className="relative flex h-2 w-2">
                {agentStatus.is_active && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                )}
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    agentStatus.is_active ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
              </span>
              <Bot className="h-3.5 w-3.5 text-indigo-300" />
              <span>
                Agent: {agentStatus.status_label || (agentStatus.is_active ? "ACTIVE" : "PAUSED")}
              </span>
              <span className="rounded-md bg-slate-800/90 px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
                {agentStatus.dispatched_today}/{agentStatus.daily_limit} DMs
              </span>
            </button>
          )}
          {/* Dual Scanner Buttons */}
          {onOpenScanInstagram && (
            <button
              onClick={onOpenScanInstagram}
              className="flex items-center gap-1.5 rounded-xl border border-pink-500/40 bg-pink-500/10 px-3 py-1.5 text-xs font-semibold text-pink-300 transition-all hover:bg-pink-500/20 hover:border-pink-500/60 active:scale-95 shadow-sm"
            >
              <Instagram className="h-3.5 w-3.5 text-pink-400" />
              <span>Scan IG Intent</span>
            </button>
          )}

          {onOpenScanMaps && (
            <button
              onClick={onOpenScanMaps}
              className="flex items-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition-all hover:bg-emerald-500/20 hover:border-emerald-500/60 active:scale-95 shadow-sm"
            >
              <MapPin className="h-3.5 w-3.5 text-emerald-400" />
              <span>Scan Maps Leads</span>
            </button>
          )}

          {/* Daily IG Auto-DM Batch Dispatch Control */}
          {onDispatchIgBatch && (
            <div className="hidden lg:flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-xs">
              <span className="text-slate-400 text-[11px] font-medium">Daily Limit:</span>
              <input
                type="number"
                min={1}
                max={50}
                value={dailyIgLimit}
                onChange={(e) => onDailyIgLimitChange && onDailyIgLimitChange(parseInt(e.target.value) || 15)}
                className="w-10 rounded-lg bg-slate-800 px-1 py-0.5 text-center text-xs font-bold text-white outline-none border border-slate-700"
                title="Configurable daily Instagram DM limit"
              />
              <button
                onClick={onDispatchIgBatch}
                disabled={isDispatchingIg}
                className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-pink-600 to-rose-600 px-2.5 py-1 text-xs font-bold text-white hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all shadow-sm"
                title="Dispatch queued Instagram DMs with humanized pacing"
              >
                {isDispatchingIg ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Dispatching...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3 w-3" />
                    <span>Run Daily IG Batch</span>
                  </>
                )}
              </button>
              {igQueueCount > 0 && (
                <span className="rounded-full bg-pink-500/20 text-pink-300 text-[10px] font-bold px-1.5 py-0.5 border border-pink-500/30" title="Pending in queue">
                  {igQueueCount} queued
                </span>
              )}
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            title="Refresh Leads & Stats"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 transition-colors hover:border-slate-700 hover:bg-slate-800 hover:text-white"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>

          {/* Seed Sample Leads Button */}
          <button
            onClick={onSeedData}
            disabled={isSeeding}
            className="hidden sm:flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1.5 text-xs font-medium text-indigo-300 transition-all hover:bg-indigo-500/20 disabled:opacity-50"
          >
            <Database className="h-3 w-3 text-indigo-400" />
            <span>{isSeeding ? "Seeding..." : "Seed Demo"}</span>
          </button>

          {/* Swagger Docs Link */}
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden xl:flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-slate-700 hover:bg-slate-800 hover:text-white"
          >
            <span>Docs</span>
            <ExternalLink className="h-3 w-3 text-slate-400" />
          </a>
        </div>
      </div>
    </header>
  );
};
