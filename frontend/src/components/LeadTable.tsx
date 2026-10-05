"use client";

import React, { useState } from "react";
import {
  Instagram,
  ExternalLink,
  MessageSquare,
  Sparkles,
  Send,
  Clock,
  CheckCircle2,
  Trash2,
  Eye,
  Flame,
  Copy,
  Check,
  RefreshCw,
  Hash,
  Share2
} from "lucide-react";
import { Lead } from "@/types/lead";

export function getLeadPriority(lead: Lead): "High" | "Medium" | "Low" {
  if (lead.lead_score >= 80) return "High";
  if (lead.lead_score >= 50) return "Medium";
  return "Low";
}

export function formatGrowthGridDM(
  lead: { business_name?: string | null; instagram_handle?: string | null },
  existingDM?: string | null
): string {
  if (existingDM && existingDM.trim() && existingDM.includes("— GrowthGrid")) {
    return existingDM.trim();
  }
  const name = (lead.business_name && lead.business_name.trim())
    ? lead.business_name.trim()
    : ((lead.instagram_handle && lead.instagram_handle.trim()) ? lead.instagram_handle.replace(/^@/, "").trim() : "your business");
  return `Hi 👋\n\nI create modern websites for businesses and I’d love to make a free demo website for ${name}. 🌐\n\nYou can check the demo first, and if you like it, we can discuss the next steps and pricing. No pressure! 😊\n\nShould I create a demo for you?\n\n— GrowthGrid`;
}

interface LeadTableProps {
  leads: Lead[];
  loading: boolean;
  onSelectLead: (lead: Lead) => void;
  onDeleteLead: (lead: Lead) => void;
  onQueueLead?: (id: number) => Promise<void>;
  onMarkSent?: (id: number) => Promise<void>;
  onRegenerateDM?: (id: number) => Promise<void>;
  onNotify?: (message: string, type?: "success" | "error") => void;
  onOpenScanPosts: () => void;
}

export const LeadTable: React.FC<LeadTableProps> = ({
  leads,
  loading,
  onSelectLead,
  onDeleteLead,
  onQueueLead,
  onMarkSent,
  onRegenerateDM,
  onNotify,
  onOpenScanPosts,
}) => {
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Intent Detected":
      case "new":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-300">
            <span>🎯</span> Intent Detected
          </span>
        );
      case "DM Drafted":
      case "Outreach Ready":
      case "outreach_generated":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-950/60 border border-amber-800/60 px-2.5 py-0.5 text-[11px] font-semibold text-amber-300">
            <span>✍️</span> DM Drafted
          </span>
        );
      case "DM Queued":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-purple-950/60 border border-purple-800/60 px-2.5 py-0.5 text-[11px] font-semibold text-purple-300 animate-pulse">
            <Clock className="h-3 w-3" /> DM Queued
          </span>
        );
      case "Sent":
      case "Pitch Sent":
      case "contacted":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">
            <CheckCircle2 className="h-3 w-3" /> Sent
          </span>
        );
      case "converted":
      case "Closed":
      case "Deal Won 🎉":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/80 border border-emerald-500/60 px-2.5 py-0.5 text-[11px] font-bold text-emerald-200">
            <span>🎉</span> Won
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-slate-800 border border-slate-700 px-2.5 py-0.5 text-[11px] font-medium text-slate-300 capitalize">
            {status}
          </span>
        );
    }
  };

  const handleCopyPitch = async (lead: Lead) => {
    const formattedMessage = formatGrowthGridDM(lead, lead.outreach_instagram_dm);
    try {
      await navigator.clipboard.writeText(formattedMessage);
      setCopiedId(lead.id);
      setTimeout(() => setCopiedId(null), 2000);
      onNotify?.("GrowthGrid pitch copied! Just paste (Ctrl+V) in the Instagram chat.", "success");
    } catch {
      onNotify?.("Failed to copy pitch to clipboard", "error");
    }
  };

  const handleOpenInstagramDM = async (lead: Lead) => {
    const username = (lead.instagram_handle || "instagram").replace("@", "").trim();
    const formattedMessage = formatGrowthGridDM(lead, lead.outreach_instagram_dm);

    // 1. Immediately execute navigator.clipboard.writeText(formattedMessage)
    try {
      await navigator.clipboard.writeText(formattedMessage);
    } catch {
      // ignore
    }

    // 2. Display bright green toast notification
    onNotify?.("GrowthGrid pitch copied! Just paste (Ctrl+V) in the Instagram chat.", "success");

    // 3. Open https://ig.me/m/{username} in a new browser tab
    const igDirectUrl = `https://ig.me/m/${username}`;
    window.open(igDirectUrl, "_blank", "noopener,noreferrer");

    // 4. Mark status as Sent in database
    if (onMarkSent) {
      try {
        await onMarkSent(lead.id);
      } catch {
        // ignore
      }
    }
  };

  const handleQueue = async (lead: Lead) => {
    if (!onQueueLead) return;
    setActionLoadingId(lead.id);
    try {
      await onQueueLead(lead.id);
      onNotify?.(`Queued @${lead.instagram_handle?.replace('@', '')} for auto-DM dispatch!`, "success");
    } catch {
      onNotify?.("Failed to queue lead", "error");
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 glass-panel rounded-2xl">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-pink-500 border-t-transparent mb-4" />
        <p className="text-sm font-medium text-slate-400">Loading Instagram intent stream...</p>
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4 text-center glass-panel rounded-2xl border border-slate-800/80">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-pink-600/20 to-rose-600/20 border border-pink-500/30 text-pink-400 mb-4 shadow-lg shadow-pink-500/10">
          <Instagram className="h-8 w-8" />
        </div>
        <h3 className="text-base font-bold text-white">No Live Instagram Leads Detected</h3>
        <p className="mt-1.5 max-w-sm text-xs text-slate-400">
          No live inquiries matched in the active window. Trigger an autonomous AI scan across Instagram reels and posts.
        </p>
        <button
          onClick={onOpenScanPosts}
          className="mt-5 flex items-center gap-2 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-pink-500/25 hover:opacity-95 active:scale-95 transition-all"
        >
          <Sparkles className="h-4 w-4" />
          <span>Scan Live Instagram Leads (Real-Time)</span>
        </button>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-950/60 shadow-xl backdrop-blur-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="py-3.5 pl-4 pr-3">Prospect (@handle & Business)</th>
              <th className="py-3.5 px-3">Intent Score</th>
              <th className="py-3.5 px-3">Post Topic & Link</th>
              <th className="py-3.5 px-3 min-w-[240px]">Exact Buyer Comment</th>
              <th className="py-3.5 px-3 min-w-[280px]">Tailored GrowthGrid Template Preview</th>
              <th className="py-3.5 px-3">Dispatch Status</th>
              <th className="py-3.5 pl-3 pr-4 text-right">Quick Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {leads.map((lead) => {
              const handleClean = (lead.instagram_handle || "prospect").replace("@", "").trim();
              const profileUrl = `https://instagram.com/${handleClean}`;
              const postUrl = lead.source_post_url || (lead.notes?.match(/https:\/\/instagram\.com\/p\/[^\s\n]+/)?.[0]) || profileUrl;
              const postCodeMatch = postUrl.match(/\/p\/([a-zA-Z0-9_-]+)/);
              const postCode = postCodeMatch ? postCodeMatch[1] : "Reel";

              const commentDisplay = lead.comment_text || (lead.notes?.split("Original Comment:")[1]?.split("\n")[0]?.trim()) || (lead.score_reasons || "Commercial inquiry captured");

              // Extract post freshness / time frame badge (e.g. "Posted 2d ago")
              const matchAge = lead.notes?.match(/Posted:\s*([^\n]+)/i) || lead.score_reasons?.match(/Posted:\s*([^\n•]+)/i);
              let postAgeBadge = matchAge ? `Posted ${matchAge[1].trim()}` : null;
              if (!postAgeBadge) {
                const createdDate = new Date(lead.created_at);
                const now = new Date();
                const diffHours = Math.max(1, Math.floor((now.getTime() - createdDate.getTime()) / (1000 * 60 * 60)));
                if (diffHours < 24) {
                  postAgeBadge = `Posted ${diffHours}h ago`;
                } else {
                  const diffDays = Math.floor(diffHours / 24);
                  postAgeBadge = `Posted ${diffDays}d ago`;
                }
              }

              return (
                <tr
                  key={lead.id}
                  className="group hover:bg-slate-900/40 transition-colors"
                >
                  {/* Lead Profile */}
                  <td className="py-3 pl-4 pr-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-pink-600 via-rose-600 to-amber-500 text-white font-bold text-xs shadow-md shadow-pink-500/10">
                        {handleClean.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <a
                          href={profileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 font-bold text-white hover:text-pink-400 transition-colors truncate"
                          title="Open Instagram Profile"
                        >
                          <span>@{handleClean}</span>
                          <ExternalLink className="h-3 w-3 flex-shrink-0 text-slate-500" />
                        </a>
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-0.5">
                          <span className="truncate max-w-[130px]">{lead.business_name}</span>
                          {lead.industry && (
                            <span className="rounded bg-slate-800/80 px-1.5 py-0.2 text-[10px] text-pink-300 font-medium border border-slate-700/60">
                              {lead.industry}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Intent Score */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <div className="flex items-center gap-1 rounded-lg bg-pink-500/10 border border-pink-500/30 px-2 py-1 text-xs font-bold text-pink-300">
                        <Flame className="h-3.5 w-3.5 text-pink-400 fill-pink-400/20" />
                        <span>{lead.lead_score}%</span>
                      </div>
                    </div>
                  </td>

                  {/* Post Topic & Link */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="inline-block rounded-md bg-pink-500/10 border border-pink-500/20 px-2 py-0.5 text-[10px] font-semibold text-pink-300 max-w-[130px] truncate">
                          {lead.industry || "Business Growth"}
                        </span>
                        {/* Selected time frame badge: e.g. "Posted 2d ago" */}
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-800/90 border border-slate-700/80 px-2 py-0.5 text-[10px] font-medium text-amber-300">
                          <Clock className="h-2.5 w-2.5 text-amber-400" />
                          <span>{postAgeBadge}</span>
                        </span>
                      </div>
                      <div>
                        <a
                          href={postUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded bg-slate-900 border border-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300 hover:text-white hover:border-slate-700 transition-all"
                        >
                          <Hash className="h-2.5 w-2.5 text-pink-400" />
                          <span>p/{postCode.slice(0, 8)}</span>
                          <ExternalLink className="h-2.5 w-2.5 text-slate-500 ml-0.5" />
                        </a>
                      </div>
                    </div>
                  </td>

                  {/* Exact Buyer Comment */}
                  <td className="py-3 px-3">
                    <div className="rounded-xl border border-slate-800/90 bg-slate-900/60 p-2 text-[11px] text-slate-300 font-mono leading-relaxed max-w-sm">
                      <span className="text-pink-400 font-bold mr-1">“</span>
                      <span>{commentDisplay.replace(/^“|”$/g, '')}</span>
                      <span className="text-pink-400 font-bold ml-1">”</span>
                    </div>
                  </td>

                  {/* Tailored GrowthGrid Template Preview */}
                  <td className="py-3 px-3">
                    <div className="relative rounded-xl border border-pink-500/20 bg-pink-500/5 p-2.5 text-[11px] text-slate-200 leading-relaxed max-w-md group/dm">
                      <div className="flex items-center justify-between pb-1 mb-1 border-b border-pink-500/20 text-[10px] text-pink-300 font-semibold">
                        <span className="flex items-center gap-1">
                          <Sparkles className="h-3 w-3 text-pink-400" />
                          <span>GrowthGrid Demo Offer</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => handleCopyPitch(lead)}
                          className="flex items-center gap-1 rounded px-1.5 py-0.5 bg-pink-500/10 hover:bg-pink-500/20 text-pink-300 transition-colors"
                          title="Copy GrowthGrid pitch to clipboard"
                        >
                          {copiedId === lead.id ? (
                            <>
                              <Check className="h-2.5 w-2.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-2.5 w-2.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                      <p className="line-clamp-2 text-slate-300 font-sans whitespace-pre-line">
                        {formatGrowthGridDM(lead, lead.outreach_instagram_dm)}
                      </p>
                    </div>
                  </td>

                  {/* Dispatch Status */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    {getStatusBadge(lead.status)}
                  </td>

                  {/* Quick Actions */}
                  <td className="py-3 pl-3 pr-4 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Open Instagram DM button */}
                      <button
                        type="button"
                        onClick={() => handleOpenInstagramDM(lead)}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 px-3 py-1.5 text-[11px] font-bold text-white shadow-md shadow-pink-500/20 hover:opacity-90 active:scale-95 transition-all"
                        title="Copy GrowthGrid pitch & open direct message in Instagram"
                      >
                        <Send className="h-3 w-3" />
                        <span>Open Instagram DM</span>
                      </button>

                      {/* Separate small Copy Pitch button */}
                      <button
                        type="button"
                        onClick={() => handleCopyPitch(lead)}
                        className="inline-flex items-center gap-1 rounded-xl border border-slate-700 bg-slate-800/90 hover:bg-slate-700 px-2 py-1.5 text-[11px] font-semibold text-slate-300 hover:text-white transition-all active:scale-95"
                        title="Copy GrowthGrid pitch text to clipboard"
                      >
                        {copiedId === lead.id ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-400" />
                            <span className="text-emerald-400 text-[10px]">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3 text-pink-400" />
                            <span className="text-[10px]">Copy Pitch</span>
                          </>
                        )}
                      </button>

                      {/* Queue for Auto-DM */}
                      {lead.status !== "DM Queued" && lead.status !== "Sent" && (
                        <button
                          type="button"
                          onClick={() => handleQueue(lead)}
                          disabled={actionLoadingId === lead.id}
                          className="inline-flex items-center gap-1 rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 px-2.5 py-1.5 text-[11px] font-semibold text-purple-300 transition-all disabled:opacity-50"
                          title="Queue for background rate-limited auto-DM dispatch"
                        >
                          <Clock className="h-3 w-3" />
                          <span>Queue</span>
                        </button>
                      )}

                      {/* View Drawer */}
                      <button
                        type="button"
                        onClick={() => onSelectLead(lead)}
                        className="rounded-xl border border-slate-800 bg-slate-900 p-1.5 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
                        title="View Full Lead & Edit Outreach"
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </button>

                      {/* Delete */}
                      <button
                        type="button"
                        onClick={() => onDeleteLead(lead)}
                        className="rounded-xl border border-slate-800 bg-slate-900 p-1.5 text-slate-400 hover:text-rose-400 hover:border-rose-900/60 transition-colors"
                        title="Delete Prospect"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
