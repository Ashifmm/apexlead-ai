"use client";

import React, { useState, useEffect } from "react";
import { X, MapPin, Sparkles, Loader2, Zap, Layers, Globe, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

interface ScanMapsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (params: { niche: string; city: string; count: number; mode: "direct" | "browser" }) => Promise<void>;
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
  const [mode, setMode] = useState<"direct" | "browser">("direct");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState<number>(0);

  // Animate loading steps when active
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isLoading) {
      setErrorMsg(null);
      setLoadingStep(0);
      timer = setInterval(() => {
        setLoadingStep((prev) => (prev < 3 ? prev + 1 : prev));
      }, 2500);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(timer);
  }, [isLoading]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!niche.trim() || !city.trim()) return;
    setErrorMsg(null);
    try {
      await onScan({ niche: niche.trim(), city: city.trim(), count, mode });
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to scan prospects. Try switching to Fast Direct Search mode.");
    }
  };

  const handleRetryDirect = async () => {
    setMode("direct");
    setErrorMsg(null);
    try {
      await onScan({ niche: niche.trim(), city: city.trim(), count, mode: "direct" });
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to scan prospects.");
    }
  };

  const loadingStages = [
    `Connecting to Google Maps & searching "${niche}" in ${city}...`,
    "Filtering 4.0+★ verified businesses with NO official website...",
    "Compiling responsive multi-page Tailwind website showcase demos...",
    "Formatting personalized WhatsApp & cold outreach pitches..."
  ];

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

        {/* Error Alert with Quick Fallback Action */}
        {errorMsg && (
          <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-300">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0 text-rose-400 mt-0.5" />
              <div>
                <p className="font-semibold text-rose-200">Scraping Error Encountered</p>
                <p className="mt-0.5 text-rose-300/90">{errorMsg}</p>
                {mode === "browser" && (
                  <button
                    type="button"
                    onClick={handleRetryDirect}
                    className="mt-2.5 inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-1 text-xs font-semibold text-white hover:bg-rose-500 transition-colors"
                  >
                    <span>Instant Retry with Fast Direct Search</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Real Loading State Steps */}
        {isLoading ? (
          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center gap-2.5 mb-3">
              <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
              <span className="text-xs font-bold text-slate-200">Autonomous Pipeline Running...</span>
            </div>
            <div className="space-y-2.5">
              {loadingStages.map((stage, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  {idx < loadingStep ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                  ) : idx === loadingStep ? (
                    <Loader2 className="h-4 w-4 text-teal-400 animate-spin flex-shrink-0" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border border-slate-700 flex-shrink-0" />
                  )}
                  <span className={idx <= loadingStep ? "text-slate-200 font-medium" : "text-slate-500"}>
                    {stage}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Form */
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

            {/* Engine Search Mode Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Intake Engine Mode
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setMode("direct")}
                  className={`flex flex-col items-start p-2.5 rounded-xl border text-left transition-all ${
                    mode === "direct"
                      ? "border-emerald-500 bg-emerald-500/10 text-white ring-1 ring-emerald-500/30"
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                    <Zap className="h-3.5 w-3.5" />
                    <span>Fast Direct Search</span>
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5">
                    1-2s intake via Places API / HTTP (Cloud & Render safe)
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setMode("browser")}
                  className={`flex flex-col items-start p-2.5 rounded-xl border text-left transition-all ${
                    mode === "browser"
                      ? "border-emerald-500 bg-emerald-500/10 text-white ring-1 ring-emerald-500/30"
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-1.5 text-xs font-bold text-teal-400">
                    <Globe className="h-3.5 w-3.5" />
                    <span>Live Headless Browser</span>
                  </div>
                  <span className="text-[10px] text-slate-400 mt-0.5">
                    Playwright Chromium with auto-fallback to HTTP
                  </span>
                </button>
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
                <Layers className="h-4 w-4" />
                <span>
                  {mode === "direct" ? "Fast Search & Generate Demos" : "Deep Scan & Generate Demos"}
                </span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
