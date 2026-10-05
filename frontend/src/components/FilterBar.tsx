"use client";

import React from "react";
import { Search, Plus, Filter, Flame, Briefcase, X, Instagram, Send, Sparkles } from "lucide-react";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusChange: (status: string) => void;
  priorityFilter: string;
  onPriorityChange: (priority: string) => void;
  industryFilter: string;
  onIndustryChange: (industry: string) => void;
  availableIndustries: string[];
  onOpenCreateModal: () => void;
  onOpenScanPostsModal: () => void;
  onDispatchBatch: () => void;
  isDispatching: boolean;
}

const statusOptions = [
  { id: "all", label: "All Prospects" },
  { id: "Intent Detected", label: "Intent Detected 🎯" },
  { id: "DM Drafted", label: "DM Drafted ✍️" },
  { id: "DM Queued", label: "DM Queued ⏳" },
  { id: "Sent", label: "Sent 🚀" },
  { id: "converted", label: "Closed / Won 🎉" },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  priorityFilter,
  onPriorityChange,
  industryFilter,
  onIndustryChange,
  availableIndustries,
  onOpenCreateModal,
  onOpenScanPostsModal,
  onDispatchBatch,
  isDispatching,
}) => {
  const hasActiveFilters =
    search.trim() !== "" ||
    statusFilter !== "all" ||
    priorityFilter !== "all" ||
    industryFilter !== "all";

  const clearAllFilters = () => {
    onSearchChange("");
    onStatusChange("all");
    onPriorityChange("all");
    onIndustryChange("all");
  };

  return (
    <div className="space-y-3.5">
      {/* Top Row: Search, Dropdowns, Action CTAs */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        {/* Search Bar */}
        <div className="relative flex-1 max-w-lg">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by @handle, comment text, vertical, or notes..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/90 py-2.5 pl-10 pr-9 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all focus:border-pink-500/70 focus:ring-2 focus:ring-pink-500/20"
          />
          {search && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Filter Controls Row */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Priority Filter */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <Flame className="h-3.5 w-3.5 text-amber-400" />
            <select
              value={priorityFilter}
              onChange={(e) => onPriorityChange(e.target.value)}
              className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Intent: All</option>
              <option value="high" className="bg-slate-900 text-rose-400">🔥 High Intent (90%+)</option>
              <option value="medium" className="bg-slate-900 text-amber-400">⚡ Medium Intent (80%+)</option>
              <option value="low" className="bg-slate-900 text-slate-400">Low Intent</option>
            </select>
          </div>

          {/* Industry Filter */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <Briefcase className="h-3.5 w-3.5 text-pink-400" />
            <select
              value={industryFilter}
              onChange={(e) => onIndustryChange(e.target.value)}
              className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer max-w-[150px] truncate"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Niche: All</option>
              {availableIndustries.map((ind) => (
                <option key={ind} value={ind} className="bg-slate-900 text-slate-200">
                  {ind}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters button if any active */}
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="rounded-xl border border-slate-800 bg-slate-900/60 px-2.5 py-1.5 text-xs text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
            >
              Reset
            </button>
          )}

          {/* Scan Target Posts / Comments CTA */}
          <button
            onClick={onOpenScanPostsModal}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-pink-500/40 bg-gradient-to-r from-pink-600/20 via-rose-600/20 to-amber-500/10 px-3.5 py-2 text-xs font-semibold text-pink-300 shadow-sm transition-all hover:bg-pink-500/25 hover:border-pink-500/60 active:scale-[0.98]"
          >
            <Instagram className="h-4 w-4 text-pink-400" />
            <span>Scan Target Posts</span>
          </button>

          {/* Approve & Send Queued DMs CTA */}
          <button
            onClick={onDispatchBatch}
            disabled={isDispatching}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-purple-500/40 bg-purple-500/10 px-3.5 py-2 text-xs font-semibold text-purple-300 shadow-sm transition-all hover:bg-purple-500/20 hover:border-purple-500/60 active:scale-[0.98] disabled:opacity-50"
          >
            <Send className="h-4 w-4 text-purple-400" />
            <span>Approve & Send DMs</span>
          </button>

          {/* Add Manual Lead */}
          <button
            onClick={onOpenCreateModal}
            className="flex items-center justify-center gap-1.5 rounded-xl bg-slate-900 border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-300 shadow transition-all hover:text-white hover:border-slate-700 active:scale-[0.98]"
          >
            <Plus className="h-4 w-4" />
            <span>Add Lead</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Pipeline status pill filters */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        <span className="flex items-center gap-1 text-slate-500 mr-1 text-[11px] font-semibold uppercase tracking-wider">
          <Filter className="h-3 w-3" />
          Status:
        </span>
        {statusOptions.map((opt) => {
          const isActive = statusFilter === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => onStatusChange(opt.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1 font-medium transition-all ${
                isActive
                  ? "bg-pink-600 text-white shadow-sm shadow-pink-500/30"
                  : "bg-slate-900/70 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800/80"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
