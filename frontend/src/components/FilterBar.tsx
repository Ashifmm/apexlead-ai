"use client";

import React from "react";
import { Search, Plus, Filter, Flame, Globe2, Briefcase, X, Target, Instagram, MapPin } from "lucide-react";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusChange: (status: string) => void;
  hasWebsiteFilter: boolean | undefined;
  onHasWebsiteChange: (val: boolean | undefined) => void;
  priorityFilter: string;
  onPriorityChange: (priority: string) => void;
  industryFilter: string;
  onIndustryChange: (industry: string) => void;
  availableIndustries: string[];
  onOpenCreateModal: () => void;
  onOpenTargetNicheModal?: () => void;
  onOpenScanInstagramModal?: () => void;
  onOpenScanMapsModal?: () => void;
}

const statusOptions = [
  { id: "all", label: "All Statuses" },
  { id: "new", label: "New" },
  { id: "Outreach Ready", label: "Outreach Ready" },
  { id: "Pitch Sent", label: "Pitch Sent 🚀" },
  { id: "In Discussion", label: "In Discussion 💬" },
  { id: "Closed", label: "Closed / Won 🎉" },
  { id: "demo_generated", label: "Demo Ready ⚡" },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  hasWebsiteFilter,
  onHasWebsiteChange,
  priorityFilter,
  onPriorityChange,
  industryFilter,
  onIndustryChange,
  availableIndustries,
  onOpenCreateModal,
  onOpenTargetNicheModal,
  onOpenScanInstagramModal,
  onOpenScanMapsModal,
}) => {
  const hasActiveFilters =
    search.trim() !== "" ||
    statusFilter !== "all" ||
    hasWebsiteFilter !== undefined ||
    priorityFilter !== "all" ||
    industryFilter !== "all";

  const clearAllFilters = () => {
    onSearchChange("");
    onStatusChange("all");
    onHasWebsiteChange(undefined);
    onPriorityChange("all");
    onIndustryChange("all");
  };

  return (
    <div className="space-y-3.5">
      {/* Top Row: Search, Dropdowns, Add Lead CTA */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        {/* Search Bar */}
        <div className="relative flex-1 max-w-lg">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by business, niche, location, contact..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/90 py-2.5 pl-10 pr-9 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all focus:border-indigo-500/70 focus:ring-2 focus:ring-indigo-500/20"
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
              <option value="all" className="bg-slate-900 text-slate-200">Priority: All</option>
              <option value="high" className="bg-slate-900 text-rose-400">🔥 High Priority</option>
              <option value="medium" className="bg-slate-900 text-amber-400">⚡ Medium Priority</option>
              <option value="low" className="bg-slate-900 text-slate-400">Low Priority</option>
            </select>
          </div>

          {/* Website Presence Filter */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <Globe2 className="h-3.5 w-3.5 text-indigo-400" />
            <select
              value={hasWebsiteFilter === undefined ? "all" : hasWebsiteFilter ? "has_website" : "no_website"}
              onChange={(e) => {
                const val = e.target.value;
                if (val === "all") onHasWebsiteChange(undefined);
                else if (val === "no_website") onHasWebsiteChange(false);
                else if (val === "has_website") onHasWebsiteChange(true);
              }}
              className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Website: All</option>
              <option value="no_website" className="bg-slate-900 text-amber-300">🔥 No Website (High Opp)</option>
              <option value="has_website" className="bg-slate-900 text-indigo-300">🌐 Has Website (Audit/Redesign)</option>
            </select>
          </div>

          {/* Industry Filter */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900/90 px-2.5 py-1.5 text-xs">
            <Briefcase className="h-3.5 w-3.5 text-cyan-400" />
            <select
              value={industryFilter}
              onChange={(e) => onIndustryChange(e.target.value)}
              className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer max-w-[150px] truncate"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Industry: All</option>
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

          {/* Scan IG Intent Button */}
          {onOpenScanInstagramModal && (
            <button
              onClick={onOpenScanInstagramModal}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-pink-500/40 bg-pink-500/10 px-3.5 py-2 text-xs font-semibold text-pink-300 shadow-sm transition-all hover:bg-pink-500/20 hover:border-pink-500/60 active:scale-[0.98]"
            >
              <Instagram className="h-4 w-4 text-pink-400" />
              <span>Scan IG</span>
            </button>
          )}

          {/* Scan Maps Leads Button */}
          {onOpenScanMapsModal && (
            <button
              onClick={onOpenScanMapsModal}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3.5 py-2 text-xs font-semibold text-emerald-300 shadow-sm transition-all hover:bg-emerald-500/20 hover:border-emerald-500/60 active:scale-[0.98]"
            >
              <MapPin className="h-4 w-4 text-emerald-400" />
              <span>Scan Maps</span>
            </button>
          )}

          {/* Target Niche Button */}
          {onOpenTargetNicheModal && (
            <button
              onClick={onOpenTargetNicheModal}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-indigo-500/40 bg-indigo-500/10 px-3.5 py-2 text-xs font-semibold text-indigo-300 shadow-sm transition-all hover:bg-indigo-500/20 hover:border-indigo-500/60 active:scale-[0.98]"
            >
              <Target className="h-4 w-4 text-indigo-400" />
              <span>Target Niche</span>
            </button>
          )}

          {/* Add Lead Primary CTA */}
          <button
            onClick={onOpenCreateModal}
            className="flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/20 transition-all hover:opacity-95 hover:shadow-indigo-500/30 active:scale-[0.98]"
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
          Stage:
        </span>
        {statusOptions.map((opt) => {
          const isActive = statusFilter === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => onStatusChange(opt.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1 font-medium transition-all ${
                isActive
                  ? "bg-indigo-600 text-white shadow-sm shadow-indigo-500/30"
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
