"use client";

import React, { useState, useEffect } from "react";
import { X, Sparkles, Loader2, CheckCircle2, Briefcase, Zap, Layers, Calendar, Clock, ShieldCheck } from "lucide-react";

interface ScanInstagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (params: {
    niche?: string;
    days_range?: number;
    count: number;
    quantity?: number;
    exclude_existing?: boolean;
  }) => Promise<void>;
  isLoading: boolean;
}

const DATE_RANGE_OPTIONS = [
  { value: 1, label: "Last 24 Hours" },
  { value: 2, label: "Last 2 Days" },
  { value: 7, label: "Last 7 Days" },
  { value: 14, label: "Last 14 Days" },
];

const QUANTITY_OPTIONS = [5, 10, 25, 50];

export const ScanInstagramModal: React.FC<ScanInstagramModalProps> = ({
  isOpen,
  onClose,
  onScan,
  isLoading,
}) => {
  const [niche, setNiche] = useState<string>("");
  const [daysRange, setDaysRange] = useState<number>(7);
  const [count, setCount] = useState<number>(25); // Default to 25 leads
  const [excludeExisting, setExcludeExisting] = useState<boolean>(true); // Default to 100% fresh
  const [step, setStep] = useState<number>(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      setStep(0);
      interval = setInterval(() => {
        setStep((prev) => (prev < 3 ? prev + 1 : prev));
      }, 2400);
    } else {
      setStep(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onScan({
      niche: niche.trim() || undefined,
      days_range: daysRange,
      count,
      quantity: count,
      exclude_existing: excludeExisting
    });
  };

  const steps = [
    `Harvesting live Instagram posts & reels (${count} unique leads target)...`,
    "Deduplicating against database & rotating sub-niches for zero duplicates...",
    "Tier 1 & 2 AI evaluating comments for website, online store & pricing intent...",
    "Generating GrowthGrid dynamic pitches & syncing fresh leads to dashboard..."
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-pink-500/30 bg-slate-950 p-6 shadow-2xl shadow-pink-500/10">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-tr from-pink-600 via-rose-600 to-amber-500 text-white shadow-lg shadow-pink-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">AI Lead Harvester</h3>
                <span className="rounded-full bg-pink-500/10 border border-pink-500/30 px-2 py-0.5 text-[10px] font-bold text-pink-300">
                  Zero Duplicates
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                AI inspects target post contexts and evaluates comment intent to find genuine prospects who need websites.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Loading Progress State */}
        {isLoading ? (
          <div className="mt-6 rounded-xl border border-pink-500/20 bg-pink-500/5 p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-pink-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Hunting {count} Fresh Unique Leads (Zero Duplicates)...</span>
            </div>
            <div className="space-y-2.5">
              {steps.map((s, idx) => (
                <div key={idx} className="flex items-center gap-2.5 text-xs">
                  {idx < step ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                  ) : idx === step ? (
                    <Loader2 className="h-4 w-4 text-pink-400 animate-spin flex-shrink-0" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border border-slate-700 flex-shrink-0" />
                  )}
                  <span className={idx <= step ? "text-slate-200 font-medium" : "text-slate-500"}>
                    {s}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            {/* 2-Tier Explanation banner */}
            <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-3 text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Layers className="h-3.5 w-3.5 text-pink-400" />
                <span>Autonomous 2-Tier Context Analyzer:</span>
              </div>
              <p className="text-slate-400">
                Rotates through dynamic query pools to harvest genuine comments asking for websites, stores, redesigns & pricing.
              </p>
            </div>

            {/* Post Freshness / Date Range Selector */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-pink-400" />
                  <span>Post Freshness / Date Range</span>
                </label>
                <span className="text-[10px] font-mono font-bold text-pink-300 bg-pink-500/10 px-2 py-0.5 rounded border border-pink-500/20">
                  {DATE_RANGE_OPTIONS.find((o) => o.value === daysRange)?.label || `Last ${daysRange} Days`}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {DATE_RANGE_OPTIONS.map((opt) => {
                  const isSelected = daysRange === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setDaysRange(opt.value)}
                      className={`rounded-xl py-2 px-3 text-xs font-semibold border transition-all text-left flex items-center justify-between ${
                        isSelected
                          ? "border-pink-500 bg-pink-500/20 text-pink-300 shadow-sm shadow-pink-500/20"
                          : "border-slate-800 bg-slate-900 text-slate-400 hover:text-white hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Clock className={`h-3.5 w-3.5 ${isSelected ? "text-pink-400" : "text-slate-500"}`} />
                        <span>{opt.label}</span>
                      </div>
                      {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-pink-400 flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Target Quantity Selector */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Lead Target Quantity
                </label>
                <span className="text-[10px] font-mono text-slate-400 font-semibold">
                  Selected: <strong className="text-pink-300">{count} Leads</strong>
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {QUANTITY_OPTIONS.map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setCount(num)}
                    className={`rounded-xl py-2.5 text-xs font-bold border transition-all ${
                      count === num
                        ? "border-pink-500 bg-pink-500/20 text-pink-300 shadow-sm shadow-pink-500/20"
                        : "border-slate-800 bg-slate-900 text-slate-400 hover:text-white hover:border-slate-700"
                    }`}
                  >
                    {num} Leads
                  </button>
                ))}
              </div>
            </div>

            {/* Deduplication Toggle: Exclude previously harvested profiles */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 flex items-center justify-between gap-3">
              <div className="flex items-start gap-2.5 min-w-0">
                <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <label htmlFor="excludeToggle" className="text-xs font-semibold text-slate-200 cursor-pointer block">
                    Exclude previously harvested profiles
                  </label>
                  <p className="text-[11px] text-slate-400">
                    Fetch 100% fresh leads & guaranteed zero duplicate @handles
                  </p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                <input
                  id="excludeToggle"
                  type="checkbox"
                  checked={excludeExisting}
                  onChange={(e) => setExcludeExisting(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-10 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-pink-500 peer-checked:to-rose-500"></div>
              </label>
            </div>

            {/* Target Industry / Niche */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Industry / Niche <span className="text-slate-500 font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  placeholder="e.g. Salons, eCommerce, Clinics (or leave empty for general)"
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2.5 pl-10 pr-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="rounded-xl border border-slate-800 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 px-6 py-2 text-xs font-bold text-white shadow-lg shadow-pink-500/25 hover:opacity-95 active:scale-95 disabled:opacity-50 transition-all"
              >
                <Zap className="h-4 w-4" />
                <span>Start AI Discovery</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
