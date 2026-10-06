"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Instagram,
  ExternalLink,
  Flame,
  Copy,
  Check,
  Send,
  Clock,
  Sparkles,
  RefreshCw,
  Hash,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Building2,
  Calendar,
  Layers
} from "lucide-react";
import { Lead } from "@/types/lead";

interface LeadDetailModalProps {
  lead: Lead | null;
  isOpen?: boolean;
  onClose: () => void;
  onUpdateStatus: (id: number, newStatus: string) => void;
  onSaveOutreachDrafts?: (
    id: number,
    data: {
      outreach_instagram_dm?: string;
      status?: string;
      notes?: string;
    }
  ) => Promise<void>;
  onRegenerateDM?: (id: number) => Promise<void>;
  onQueueLead?: (id: number) => Promise<void>;
  onMarkSent?: (id: number) => Promise<void>;
  isRegeneratingDM?: boolean;
  onNotify?: (message: string, type?: "success" | "error") => void;
}

function getModalGrowthGridDM(
  lead: Lead,
  existingDM?: string | null
): string {
  const name = (lead.business_name && lead.business_name.trim())
    ? lead.business_name.trim()
    : ((lead.instagram_handle && lead.instagram_handle.trim()) ? lead.instagram_handle.replace(/^@/, "").trim() : "your business");
  return `Hi 👋\n\nI create modern websites for businesses and I’d love to make a free demo website for ${name}. 🌐\n\nYou can check the demo first, and if you like it, we can discuss the next steps and pricing. No pressure! 😊\n\nShould I create a demo for you?\n\n— GrowthGrid`;
}

export const LeadDetailModal: React.FC<LeadDetailModalProps> = ({
  lead,
  isOpen = true,
  onClose,
  onUpdateStatus,
  onSaveOutreachDrafts,
  onRegenerateDM,
  onQueueLead,
  onMarkSent,
  isRegeneratingDM = false,
  onNotify,
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "dm_generator">("dm_generator");
  const [draftDM, setDraftDM] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [isSaving, setIsSaving] = useState<boolean>(false);

  useEffect(() => {
    if (lead) {
      setDraftDM(getModalGrowthGridDM(lead, lead.outreach_instagram_dm));
      setNotes(lead.notes || "");
    }
  }, [lead]);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!isOpen || !lead) return null;

  const handleCopy = async (text: string, fieldName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
      onNotify?.("GrowthGrid pitch copied! Just paste (Ctrl+V) in the Instagram chat.", "success");
    } catch {
      onNotify?.("Failed to copy to clipboard", "error");
    }
  };

  const handleSave = async () => {
    if (!onSaveOutreachDrafts) return;
    setIsSaving(true);
    try {
      await onSaveOutreachDrafts(lead.id, {
        outreach_instagram_dm: draftDM,
        notes: notes,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleOneClickWebDM = async () => {
    const handleClean = (lead.instagram_handle || "instagram").replace(/^@+/, "").trim();
    const dmText = draftDM || getModalGrowthGridDM(lead, lead.outreach_instagram_dm);
    const businessName = lead.business_name || handleClean;

    // 1. Copy GrowthGrid pitch template to clipboard
    try {
      await navigator.clipboard.writeText(dmText);
    } catch {
      // ignore
    }

    // 2. Show toast: "GrowthGrid pitch copied for {business_name}!"
    onNotify?.(`GrowthGrid pitch copied for ${businessName}!`, "success");

    // 3. Open https://ig.me/m/{username} in a new tab
    const igDirectUrl = `https://ig.me/m/${handleClean}`;
    window.open(igDirectUrl, "_blank", "noopener,noreferrer");

    // 4. Mark status as Sent in database
    if (onMarkSent) {
      await onMarkSent(lead.id);
    }
  };

  const handleQueue = async () => {
    if (onQueueLead) {
      await onQueueLead(lead.id);
    }
  };

  const handleRegenerate = async () => {
    if (onRegenerateDM) {
      await onRegenerateDM(lead.id);
    }
  };

  const handleClean = (lead.instagram_handle || "prospect").replace("@", "").trim();
  const profileUrl = `https://instagram.com/${handleClean}`;
  const postUrl = lead.source_post_url || `https://instagram.com/${handleClean}`;
  const commentText = lead.comment_text || (lead.notes?.split("Original Comment:")[1]?.split("\n")[0]?.trim()) || "Commercial inquiry captured from Instagram";

  const matchAgeModal = lead.notes?.match(/Posted:\s*([^\n]+)/i) || lead.score_reasons?.match(/Posted:\s*([^\n•]+)/i);
  const postAgeModal = matchAgeModal ? `Posted ${matchAgeModal[1].trim()}` : "Recent";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/75 backdrop-blur-sm animate-in fade-in">
      <div className="relative flex h-full w-full max-w-2xl flex-col border-l border-slate-800 bg-slate-950 p-6 shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-pink-600 via-rose-600 to-amber-500 text-white font-bold text-base shadow-lg shadow-pink-500/20">
              {handleClean.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <a
                  href={profileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-base font-bold text-white hover:text-pink-400 flex items-center gap-1 transition-colors"
                >
                  <span>@{handleClean}</span>
                  <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
                </a>
                <span className="rounded-full bg-pink-500/10 border border-pink-500/30 px-2 py-0.5 text-[11px] font-bold text-pink-300">
                  {lead.lead_score}% Intent
                </span>
                <span className="rounded-full bg-slate-800/80 border border-slate-700/80 px-2 py-0.5 text-[10px] font-medium text-amber-300 flex items-center gap-1">
                  <Clock className="h-2.5 w-2.5 text-amber-400" />
                  <span>{postAgeModal}</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {lead.business_name} • {lead.industry || "Commercial Brand"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-900 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Controls */}
        <div className="flex border-b border-slate-800 mt-4 text-xs font-semibold">
          <button
            onClick={() => setActiveTab("dm_generator")}
            className={`flex items-center gap-2 pb-3 px-3 transition-colors border-b-2 ${
              activeTab === "dm_generator"
                ? "border-pink-500 text-pink-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>Tailored GrowthGrid Template Preview</span>
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 pb-3 px-3 transition-colors border-b-2 ${
              activeTab === "overview"
                ? "border-pink-500 text-pink-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Captured Comment & Context</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 py-5 space-y-5">
          {/* Status Quick Bar */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3.5 flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Pipeline Status:</span>
            <div className="flex items-center gap-2">
              <select
                value={lead.status}
                onChange={(e) => onUpdateStatus(lead.id, e.target.value)}
                className="rounded-lg bg-slate-800 border border-slate-700 px-2.5 py-1 text-xs font-semibold text-white outline-none cursor-pointer"
              >
                <option value="Intent Detected">🎯 Intent Detected</option>
                <option value="DM Drafted">✍️ DM Drafted</option>
                <option value="DM Queued">⏳ DM Queued</option>
                <option value="Sent">🚀 Sent</option>
                <option value="converted">🎉 Deal Won</option>
              </select>
            </div>
          </div>

          {/* TAB 1: TAILORED GROWTHGRID TEMPLATE PREVIEW */}
          {activeTab === "dm_generator" && (
            <div className="space-y-4">
              {/* Context formula guide */}
              <div className="rounded-xl border border-pink-500/20 bg-pink-500/5 p-3.5 text-xs text-pink-200/90 space-y-1">
                <div className="font-bold text-pink-300 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>GrowthGrid High-Converting Demo Outreach:</span>
                </div>
                <p className="text-[11px] text-slate-300">
                  Offers a free, zero-pressure demo website for <span className="text-pink-300 font-semibold">{lead.business_name || `@${handleClean}`}</span> to convert comments into paying clients.
                </p>
              </div>

              {/* Editable DM Draft Textarea */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-300">
                    Tailored Cold Direct Message
                  </label>
                  <div className="flex items-center gap-1.5">
                    {onRegenerateDM && (
                      <button
                        type="button"
                        onClick={handleRegenerate}
                        disabled={isRegeneratingDM}
                        className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold text-pink-300 hover:text-white bg-pink-500/10 hover:bg-pink-500/20 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw className={`h-3 w-3 ${isRegeneratingDM ? "animate-spin" : ""}`} />
                        <span>Regenerate with Gemini</span>
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => handleCopy(draftDM, "dm")}
                      className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                    >
                      {copiedField === "dm" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      <span>{copiedField === "dm" ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                </div>

                <textarea
                  rows={5}
                  value={draftDM}
                  onChange={(e) => setDraftDM(e.target.value)}
                  placeholder="Tailored personalized message..."
                  className="w-full rounded-xl border border-slate-800 bg-slate-900/90 p-3 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20 leading-relaxed font-sans"
                />
              </div>

              {/* Action dispatch buttons */}
              <div className="flex flex-wrap items-center gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={handleOneClickWebDM}
                  className="flex-1 min-w-[180px] flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 py-2.5 px-4 text-xs font-bold text-white shadow-lg shadow-pink-500/20 hover:opacity-95 active:scale-95 transition-all"
                  title="Copy pitch and open direct message in Instagram"
                >
                  <Send className="h-4 w-4" />
                  <span>Open Instagram DM</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleCopy(draftDM || getModalGrowthGridDM(lead, lead.outreach_instagram_dm), "dm_modal")}
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 py-2.5 px-3.5 text-xs font-semibold text-slate-200 transition-all active:scale-95"
                  title="Copy formatted pitch to clipboard"
                >
                  {copiedField === "dm_modal" ? (
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-slate-400" />
                  )}
                  <span>{copiedField === "dm_modal" ? "Copied" : "Copy Pitch"}</span>
                </button>

                <button
                  type="button"
                  onClick={handleQueue}
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-purple-500/40 bg-purple-500/10 hover:bg-purple-500/20 py-2.5 px-3 text-xs font-bold text-purple-300 transition-all active:scale-95"
                  title="Queue lead for background auto-DM scheduler"
                >
                  <Clock className="h-3.5 w-3.5" />
                  <span>Queue Auto-DM</span>
                </button>
              </div>

              {/* Save custom edits */}
              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={isSaving}
                  className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-1.5 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
                >
                  {isSaving ? "Saving..." : "Save Edits"}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: CAPTURED COMMENT & CONTEXT */}
          {activeTab === "overview" && (
            <div className="space-y-4">
              {/* Original Comment Card */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                  <span className="flex items-center gap-1.5 text-pink-400">
                    <MessageSquare className="h-4 w-4" />
                    <span>Captured Intent Comment</span>
                  </span>
                  <a
                    href={postUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white"
                  >
                    <span>View Post</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                <div className="rounded-lg bg-slate-950 p-3 text-xs text-slate-200 font-mono leading-relaxed border border-slate-800/80">
                  “{commentText}”
                </div>
              </div>

              {/* Commercial Evaluation */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Flame className="h-4 w-4 text-pink-400" />
                  <span>Commercial Intent Evaluation</span>
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {lead.score_reasons || "High-intent inquiry signaling urgent web development and ecommerce needs."}
                </p>
              </div>

              {/* Internal Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Internal Agency Notes
                </label>
                <textarea
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Notes about prospect or custom requirements..."
                  className="w-full rounded-xl border border-slate-800 bg-slate-900/90 p-3 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-1 focus:ring-pink-500/20 leading-relaxed font-sans"
                />
                <div className="mt-2 flex justify-end">
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={isSaving}
                    className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-1.5 text-xs font-semibold text-slate-200 transition-colors"
                  >
                    {isSaving ? "Saving..." : "Save Notes"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
