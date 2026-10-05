"use client";

import React, { useState } from "react";
import { X, Target, Sparkles, Loader2, AlertCircle, MapPin, Briefcase } from "lucide-react";

interface TargetNicheModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDiscover: (niche: string, city: string) => Promise<void>;
}

const POPULAR_NICHES = [
  "Luxury Salon",
  "Gym & Fitness",
  "Cafe & Bakery",
  "Dental Clinic",
  "Car Detailing",
  "Roofing & Construction",
];

const POPULAR_CITIES = [
  "Ghaziabad",
  "Delhi",
  "Noida",
  "Gurgaon",
  "Mumbai",
  "Austin",
];

export const TargetNicheModal: React.FC<TargetNicheModalProps> = ({
  isOpen,
  onClose,
  onDiscover,
}) => {
  const [niche, setNiche] = useState<string>("Luxury Salon");
  const [city, setCity] = useState<string>("Ghaziabad");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!niche.trim()) {
      setError("Please specify a target niche or vertical.");
      return;
    }
    if (!city.trim()) {
      setError("Please specify a target city or market.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await onDiscover(niche.trim(), city.trim());
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to discover niche leads.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop Overlay */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity cursor-pointer"
        onClick={() => !isLoading && onClose()}
        aria-hidden="true"
      />

      {/* Modal Container */}
      <div
        className="relative z-10 w-full max-w-lg overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-0.5 shadow-md shadow-indigo-500/20">
              <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
                <Target className="h-5 w-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Target High-Intent Niche
              </h2>
              <p className="text-xs text-slate-400">
                Phase 7 & 8: Dynamic Local Lead Generation & Scoring
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <p className="text-xs text-slate-300 leading-relaxed">
            Enter any vertical and city. ApexLead AI will scout 5 verified local businesses
            (rating &ge; 4.4, reviews &gt; 30, no active website), insert them into your pipeline,
            and formulate AI opportunity scores and customized outreach copy.
          </p>

          {/* Niche Input */}
          <div className="space-y-2">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
              <Briefcase className="h-3.5 w-3.5 text-indigo-400" />
              <span>Target Niche / Vertical *</span>
            </label>
            <input
              type="text"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g. Luxury Salon, Gym, Cafe, Dental Clinic"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500/70 focus:ring-2 focus:ring-indigo-500/20"
              disabled={isLoading}
            />
            {/* Quick Niche Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {POPULAR_NICHES.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setNiche(item)}
                  disabled={isLoading}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all ${
                    niche === item
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-700/60"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {/* City Input */}
          <div className="space-y-2">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-200">
              <MapPin className="h-3.5 w-3.5 text-pink-400" />
              <span>Target City / Market *</span>
            </label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. Ghaziabad, Delhi, Noida"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-2 focus:ring-pink-500/20"
              disabled={isLoading}
            />
            {/* Quick City Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {POPULAR_CITIES.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setCity(item)}
                  disabled={isLoading}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all ${
                    city === item
                      ? "bg-pink-600 text-white shadow-sm"
                      : "bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-700/60"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-5 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 hover:opacity-95 active:scale-95 disabled:opacity-50 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Discovering Leads...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Discover Leads</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
