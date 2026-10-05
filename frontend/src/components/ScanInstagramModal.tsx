"use client";

import React, { useState } from "react";
import { X, Instagram, Search, Sparkles, Loader2, AlertCircle } from "lucide-react";

interface ScanInstagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (params: { keyword: string; count: number }) => Promise<void>;
  isLoading: boolean;
}

const QUICK_KEYWORDS = [
  "need website",
  "looking for developer",
  "want ecommerce",
  "hire web designer",
  "shopify setup",
];

export const ScanInstagramModal: React.FC<ScanInstagramModalProps> = ({
  isOpen,
  onClose,
  onScan,
  isLoading,
}) => {
  const [keyword, setKeyword] = useState<string>("need website");
  const [count, setCount] = useState<number>(5);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    await onScan({ keyword: keyword.trim(), count });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-pink-500/30 bg-slate-950 p-6 shadow-2xl shadow-pink-500/10">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-pink-600 via-rose-600 to-amber-500 text-white shadow-md shadow-pink-500/20">
              <Instagram className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Instagram Intent Scanner</h3>
              <p className="text-xs text-slate-400">Discover leads actively expressing need for web services</p>
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

        {/* Notice Badge */}
        <div className="mt-4 rounded-xl border border-pink-500/20 bg-pink-500/10 p-3 text-xs text-pink-300 flex items-start gap-2.5">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-pink-400 mt-0.5" />
          <div>
            <span className="font-bold">Targeting Rule: </span>
            Captures handles, bios, and exact intent comments. Demo websites are{" "}
            <span className="underline font-semibold">NOT</span> auto-generated for Instagram leads.
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Intent Trigger Phrase / Keyword
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                required
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g. need website, looking for developer"
                className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2.5 pl-9 pr-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20"
              />
            </div>
            {/* Quick Pills */}
            <div className="flex flex-wrap gap-1.5 mt-2">
              {QUICK_KEYWORDS.map((kw) => (
                <button
                  key={kw}
                  type="button"
                  onClick={() => setKeyword(kw)}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    keyword === kw
                      ? "bg-pink-600 text-white font-semibold"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {kw}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Target Lead Count
            </label>
            <div className="flex items-center gap-3">
              {[3, 5, 8, 10].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setCount(num)}
                  className={`flex-1 rounded-xl py-2 text-xs font-semibold border transition-all ${
                    count === num
                      ? "border-pink-500 bg-pink-500/20 text-pink-300"
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:text-white"
                  }`}
                >
                  {num} Prospects
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="rounded-xl border border-slate-800 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !keyword.trim()}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 px-5 py-2 text-xs font-bold text-white shadow-lg shadow-pink-500/25 hover:opacity-95 active:scale-95 disabled:opacity-50 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Scanning Instagram Intent...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Scan & Intake Leads</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
