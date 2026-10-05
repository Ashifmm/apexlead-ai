"use client";

import React, { useState } from "react";
import { X, MapPin, Sparkles, Loader2, Zap, Layers } from "lucide-react";

interface ScanMapsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (params: { niche: string; city: string; count: number }) => Promise<void>;
  isLoading: boolean;
}

const POPULAR_NICHES = [
  "Dental Clinic",
  "Luxury Salon",
  "CrossFit Gym",
  "Artisan Cafe",
  "Auto Detailing",
  "Roofing Contractor",
];

const POPULAR_CITIES = [
  "Ghaziabad",
  "Delhi",
  "Noida",
  "Gurgaon",
  "Mumbai",
  "Austin",
  "New York",
];

export const ScanMapsModal: React.FC<ScanMapsModalProps> = ({
  isOpen,
  onClose,
  onScan,
  isLoading,
}) => {
  const [niche, setNiche] = useState<string>("Dental Clinic");
  const [city, setCity] = useState<string>("Ghaziabad");
  const [count, setCount] = useState<number>(5);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!niche.trim() || !city.trim()) return;
    await onScan({ niche: niche.trim(), city: city.trim(), count });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-emerald-500/30 bg-slate-950 p-6 shadow-2xl shadow-emerald-500/10">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-500/20">
              <MapPin className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Google Maps Business Finder</h3>
              <p className="text-xs text-slate-400">Discover 4.0+★ local businesses with no website</p>
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
        <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 flex items-start gap-2.5">
          <Zap className="h-4 w-4 flex-shrink-0 text-emerald-400 mt-0.5" />
          <div>
            <span className="font-bold">Automated Intake Rule: </span>
            For Google Maps leads only, the{" "}
            <span className="font-bold text-emerald-200">Ultra-Premium Demo Generator</span> is automatically
            triggered upon intake with instant live preview URLs!
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Target Vertical / Niche
            </label>
            <input
              type="text"
              required
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g. Dental Clinic, Luxury Salon, Gym"
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/20"
            />
            {/* Quick Pills */}
            <div className="flex flex-wrap gap-1.5 mt-2">
              {POPULAR_NICHES.map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setNiche(n)}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    niche === n
                      ? "bg-emerald-600 text-white font-semibold"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Target City / Location
            </label>
            <input
              type="text"
              required
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. Ghaziabad, Delhi, Noida, Austin"
              className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/20"
            />
            {/* Quick Pills */}
            <div className="flex flex-wrap gap-1.5 mt-2">
              {POPULAR_CITIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCity(c)}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    city === c
                      ? "bg-teal-600 text-white font-semibold"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Prospect Intake Count
            </label>
            <div className="flex items-center gap-3">
              {[3, 5, 8].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setCount(num)}
                  className={`flex-1 rounded-xl py-2 text-xs font-semibold border transition-all ${
                    count === num
                      ? "border-emerald-500 bg-emerald-500/20 text-emerald-300"
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:text-white"
                  }`}
                >
                  {num} Businesses
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
              disabled={isLoading || !niche.trim() || !city.trim()}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 px-5 py-2 text-xs font-bold text-white shadow-lg shadow-emerald-500/25 hover:opacity-95 active:scale-95 disabled:opacity-50 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Scraping & Generating Demos...</span>
                </>
              ) : (
                <>
                  <Layers className="h-4 w-4" />
                  <span>Scan & Auto-Generate Demos</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
