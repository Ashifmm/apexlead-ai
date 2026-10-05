"use client";

import React, { useState, useEffect } from "react";
import { X, Instagram, Search, Sparkles, Loader2, Hash, AtSign, CheckCircle2 } from "lucide-react";

interface ScanInstagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (params: { hashtag?: string; keyword?: string; target_account?: string; count: number }) => Promise<void>;
  isLoading: boolean;
}

const POPULAR_HASHTAGS = [
  "needwebsite",
  "webdesign",
  "ecommercebrand",
  "smallbusinessowner",
  "salondesign",
  "interiordesigner",
  "boutiqueowner",
  "dentalclinic",
];

const INTENT_KEYWORDS = [
  "need a website",
  "cost",
  "dm me",
  "website price",
  "portfolio",
  "revamp",
  "shopify",
  "looking for developer",
];

export const ScanInstagramModal: React.FC<ScanInstagramModalProps> = ({
  isOpen,
  onClose,
  onScan,
  isLoading,
}) => {
  const [hashtag, setHashtag] = useState<string>("needwebsite");
  const [keyword, setKeyword] = useState<string>("need a website");
  const [targetAccount, setTargetAccount] = useState<string>("");
  const [count, setCount] = useState<number>(5);
  const [step, setStep] = useState<number>(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      setStep(0);
      interval = setInterval(() => {
        setStep((prev) => (prev < 3 ? prev + 1 : prev));
      }, 2000);
    } else {
      setStep(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onScan({
      hashtag: hashtag.replace("#", "").trim(),
      keyword: keyword.trim(),
      target_account: targetAccount.replace("@", "").trim() || undefined,
      count
    });
  };

  const steps = [
    `Searching recent public posts & reels under #${hashtag}...`,
    `Filtering comments for purchase intent triggers ("${keyword}")...`,
    "Parsing commenter needs and evaluating commercial intent scores...",
    "Generating Context-Aware tailored cold outreach DMs with Gemini AI..."
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-pink-500/30 bg-slate-950 p-6 shadow-2xl shadow-pink-500/10">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-pink-600 via-rose-600 to-amber-500 text-white shadow-md shadow-pink-500/20">
              <Instagram className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Scan Target Posts / Comments</h3>
              <p className="text-xs text-slate-400">Harvest active website buyers & auto-craft tailored DMs</p>
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
          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-pink-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Scanning Instagram Community Activity...</span>
            </div>
            <div className="space-y-2">
              {steps.map((s, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
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
            {/* Target Hashtag */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Hashtag / Community Feed
              </label>
              <div className="relative">
                <Hash className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={hashtag}
                  onChange={(e) => setHashtag(e.target.value)}
                  placeholder="e.g. needwebsite, webdesign, smallbusinessowner"
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2.5 pl-9 pr-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20"
                />
              </div>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {POPULAR_HASHTAGS.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => setHashtag(tag)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                      hashtag.replace("#", "") === tag
                        ? "bg-pink-600 text-white font-semibold"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            </div>

            {/* Intent Filter Phrase */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Comment Intent Trigger Phrase
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="e.g. need a website, cost, dm me, shopify"
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2.5 pl-9 pr-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20"
                />
              </div>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {INTENT_KEYWORDS.map((kw) => (
                  <button
                    key={kw}
                    type="button"
                    onClick={() => setKeyword(kw)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition-colors ${
                      keyword === kw
                        ? "bg-rose-600 text-white font-semibold"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    "{kw}"
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Target Competitor Profile */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Competitor / Agency Profile (Optional)
              </label>
              <div className="relative">
                <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  value={targetAccount}
                  onChange={(e) => setTargetAccount(e.target.value)}
                  placeholder="e.g. webflow, shopify, squarespace"
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 py-2.5 pl-9 pr-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20"
                />
              </div>
            </div>

            {/* Lead Count */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Prospects to Capture
              </label>
              <div className="flex items-center gap-3">
                {[3, 5, 8, 12].map((num) => (
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
                    {num} Leads
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
                disabled={isLoading || !hashtag.trim() || !keyword.trim()}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 px-5 py-2 text-xs font-bold text-white shadow-lg shadow-pink-500/25 hover:opacity-95 active:scale-95 disabled:opacity-50 transition-all"
              >
                <Sparkles className="h-4 w-4" />
                <span>Scan & Draft AI DMs</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
