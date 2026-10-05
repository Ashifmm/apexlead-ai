"use client";

import React from "react";
import {
  Sparkles,
  Database,
  ExternalLink,
  RefreshCw,
  Instagram,
  Send,
  Loader2,
  Bot,
  Activity,
  Power
} from "lucide-react";
import { AgentStatus, BACKEND_HOST } from "@/lib/api";

interface HeaderProps {
  isBackendConnected: boolean;
  isSeeding: boolean;
  onSeedData: () => void;
  onRefresh: () => void;
  onOpenScanPosts: () => void;
  dailyIgLimit?: number;
  onDailyIgLimitChange?: (limit: number) => void;
  onDispatchIgBatch?: () => void;
  isDispatchingIg?: boolean;
  agentStatus?: AgentStatus | null;
  onToggleAgent?: () => void;
  onOpenAgentStream?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isBackendConnected,
  isSeeding,
  onSeedData,
  onRefresh,
  onOpenScanPosts,
  dailyIgLimit = 15,
  onDailyIgLimitChange,
  onDispatchIgBatch,
  isDispatchingIg = false,
  agentStatus,
  onToggleAgent,
  onOpenAgentStream,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand & Mission Badge */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-pink-500 via-rose-500 to-amber-500 p-0.5 shadow-lg shadow-pink-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Instagram className="h-5 w-5 text-pink-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                GrowthGrid{" "}
                <span className="bg-gradient-to-r from-pink-400 via-rose-300 to-amber-400 bg-clip-text text-transparent">
                  PRO
                </span>
              </h1>
              <span className="rounded-full border border-pink-500/30 bg-pink-500/10 px-2 py-0.5 text-[11px] font-bold text-pink-300">
                100% Pure Instagram Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Live Real-Time Lead Harvester • Instant Pitch Auto-Copy • Zero Mock Data
            </p>
          </div>
        </div>

        {/* Right Actions & Automation Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Daily Auto-Pilot Toggle & Stream Indicator */}
          {agentStatus && (
            <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 p-1">
              <button
                onClick={onOpenAgentStream}
                title="View real-time autonomous telemetry activity stream"
                className={`flex items-center gap-2 rounded-lg px-2.5 py-1 text-xs font-bold transition-all ${
                  agentStatus.is_active
                    ? "bg-emerald-950/50 text-emerald-300 hover:bg-emerald-900/50"
                    : "bg-amber-950/50 text-amber-300 hover:bg-amber-900/50"
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
                <Bot className="h-3.5 w-3.5" />
                <span>Auto-Pilot: {agentStatus.status_label || (agentStatus.is_active ? "ACTIVE" : "PAUSED")}</span>
                <span className="rounded bg-slate-800 px-1 py-0.5 text-[10px] text-slate-300 font-mono">
                  {agentStatus.dispatched_today}/{agentStatus.daily_limit}
                </span>
              </button>

              {onToggleAgent && (
                <button
                  onClick={onToggleAgent}
                  title={agentStatus.is_active ? "Pause autonomous auto-pilot" : "Resume autonomous auto-pilot"}
                  className="rounded-lg p-1 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  <Power className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          )}

          {/* Scan Target Posts Button */}
          <button
            onClick={onOpenScanPosts}
            className="flex items-center gap-1.5 rounded-xl border border-pink-500/40 bg-gradient-to-r from-pink-600/20 via-rose-600/20 to-amber-500/10 px-3 py-1.5 text-xs font-semibold text-pink-300 transition-all hover:bg-pink-500/25 hover:border-pink-500/60 active:scale-95 shadow-sm"
          >
            <Sparkles className="h-3.5 w-3.5 text-pink-400" />
            <span>Scan Target Posts</span>
          </button>

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
                title="Dispatch queued Instagram DMs with safe humanized delays"
              >
                {isDispatchingIg ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Dispatching...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3 w-3" />
                    <span>Approve & Send DMs</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            title="Refresh Prospects & Stats"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/60 text-slate-300 transition-colors hover:border-slate-700 hover:bg-slate-800 hover:text-white"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>

          {/* Seed Sample Leads Button */}
          <button
            onClick={onSeedData}
            disabled={isSeeding}
            className="hidden sm:flex items-center gap-1.5 rounded-lg border border-pink-500/30 bg-pink-500/10 px-2.5 py-1.5 text-xs font-medium text-pink-300 transition-all hover:bg-pink-500/20 disabled:opacity-50"
          >
            <Database className="h-3 w-3 text-pink-400" />
            <span>{isSeeding ? "Seeding..." : "Seed Demo"}</span>
          </button>

          {/* Swagger Docs Link */}
          <a
            href={`${BACKEND_HOST}/docs`}
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
