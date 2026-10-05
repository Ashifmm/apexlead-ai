"use client";

import React from "react";
import {
  Globe,
  ExternalLink,
  Mail,
  Phone,
  Instagram,
  Eye,
  Edit2,
  Trash2,
  Sparkles,
  AlertCircle,
  Building2,
  MapPin,
  Flame,
  Zap,
  Loader2,
  CheckCircle2,
  Layout,
  MessageSquare,
  Send,
} from "lucide-react";
import { Lead } from "@/types/lead";

interface LeadTableProps {
  leads: Lead[];
  loading: boolean;
  onSelectLead: (lead: Lead) => void;
  onEditLead: (lead: Lead) => void;
  onDeleteLead: (lead: Lead) => void;
  onSeedDemo: () => void;
  onOpenCreate: () => void;
  onAnalyzeLead?: (lead: Lead) => void;
  analyzingLeadId?: number | null;
  onQuickStatusUpdate?: (id: number, newStatus: string) => void;
  onNotify?: (message: string, type?: "success" | "error") => void;
}

export function getLeadPriority(lead: Lead): "high" | "medium" | "low" {
  const reasons = (lead.score_reasons || "").toLowerCase();
  if (reasons.includes("priority: high")) return "high";
  if (reasons.includes("priority: medium")) return "medium";
  if (reasons.includes("priority: low")) return "low";
  if (lead.lead_score >= 75) return "high";
  if (lead.lead_score >= 45) return "medium";
  return "low";
}

export const LeadTable: React.FC<LeadTableProps> = ({
  leads,
  loading,
  onSelectLead,
  onEditLead,
  onDeleteLead,
  onSeedDemo,
  onOpenCreate,
  onAnalyzeLead,
  analyzingLeadId,
  onQuickStatusUpdate,
  onNotify,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Outreach Ready":
      case "outreach_generated":
        return <span className="rounded-full bg-purple-950/60 border border-purple-800/60 px-2.5 py-0.5 text-xs font-medium text-purple-300">Outreach Ready</span>;
      case "Pitch Sent":
      case "contacted":
        return <span className="rounded-full bg-amber-950/60 border border-amber-800/60 px-2.5 py-0.5 text-xs font-medium text-amber-300">Pitch Sent</span>;
      case "In Discussion":
        return <span className="rounded-full bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 text-xs font-medium text-cyan-300">In Discussion</span>;
      case "Deal Won 🎉":
      case "Closed":
      case "converted":
        return <span className="rounded-full bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-0.5 text-xs font-medium text-emerald-300">Closed / Won 🎉</span>;
      case "Not Interested":
        return <span className="rounded-full bg-rose-950/60 border border-rose-800/60 px-2.5 py-0.5 text-xs font-medium text-rose-300">Not Interested</span>;
      case "Demo Ready":
      case "demo_generated":
        return <span className="rounded-full bg-indigo-950/60 border border-indigo-800/60 px-2.5 py-0.5 text-xs font-medium text-indigo-300">Demo Ready</span>;
      case "new":
      case "New":
        return <span className="rounded-full bg-slate-800 border border-slate-700 px-2.5 py-0.5 text-xs font-medium text-slate-300">New</span>;
      case "analyzed":
        return <span className="rounded-full bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 text-xs font-medium text-cyan-300">Analyzed</span>;
      case "scored":
        return <span className="rounded-full bg-blue-950/60 border border-blue-800/60 px-2.5 py-0.5 text-xs font-medium text-blue-300">Scored</span>;
      default:
        return <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-300 capitalize">{status}</span>;
    }
  };

  const getTableWhatsAppPitch = (lead: Lead) => {
    if (
      lead.outreach_instagram_dm &&
      lead.outreach_instagram_dm.startsWith("Hey ") &&
      lead.outreach_instagram_dm.includes("★ reviews on Google Maps")
    ) {
      return lead.outreach_instagram_dm;
    }
    const ratingMatch = (lead.notes || "").match(/(\d+\.\d+)★/);
    const rating = ratingMatch ? ratingMatch[1] : (lead.lead_score >= 90 ? "4.8" : "4.6");
    let city = "your city";
    if (lead.location) {
      const parts = lead.location.split(",");
      city = parts[parts.length - 1].trim();
    }
    const niche = lead.industry || "your industry";
    const demoUrl = lead.demo_url || `http://localhost:8000/demos/${lead.id}/`;

    return (
      `Hey ${lead.business_name}, noticed your stellar ${rating}★ reviews on Google Maps!\n\n` +
      `Local customers in ${city} are searching for ${niche}, but couldn't find your official website.\n\n` +
      `We crafted a modern, responsive showcase preview for you: ${demoUrl}\n\n` +
      `Take a 30-second look. Open to feedback!`
    );
  };

  const handleTableWhatsAppClick = (e: React.MouseEvent, lead: Lead) => {
    e.stopPropagation();
    const digits = (lead.phone || "").replace(/\D/g, "");
    const waPhone = digits.length === 10 ? `91${digits}` : digits || "919811001122";
    const pitchText = getTableWhatsAppPitch(lead);
    const waUrl = `https://api.whatsapp.com/send?phone=${waPhone}&text=${encodeURIComponent(pitchText)}`;
    window.open(waUrl, "_blank", "noopener,noreferrer");
    if (onQuickStatusUpdate) {
      onQuickStatusUpdate(lead.id, "Pitch Sent");
    }
    if (onNotify) {
      onNotify(`Opened WhatsApp for ${lead.business_name} & updated status to "Pitch Sent"`, "success");
    }
  };

  const handleTableInstagramClick = (e: React.MouseEvent, lead: Lead) => {
    e.stopPropagation();
    const handle = (lead.instagram_handle || "").replace("@", "").trim();
    const pitch = lead.outreach_instagram_dm || `Hey ${lead.business_name}! Noticed your recent interest in website development. We'd love to share some ideas!`;
    navigator.clipboard.writeText(pitch);
    const targetUrl = handle ? `https://ig.me/m/${handle}` : "https://ig.me/m/";
    window.open(targetUrl, "_blank", "noopener,noreferrer");
    if (onQuickStatusUpdate) {
      onQuickStatusUpdate(lead.id, "Pitch Sent");
    }
    if (onNotify) {
      onNotify(`Copied IG pitch & opening DM for @${handle || lead.business_name}!`, "success");
    }
  };

  const getPriorityBadge = (lead: Lead) => {
    const priority = getLeadPriority(lead);
    if (priority === "high") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 text-[11px] font-semibold text-rose-400">
          <Flame className="h-3 w-3" />
          High
        </span>
      );
    }
    if (priority === "medium") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[11px] font-semibold text-amber-400">
          <Zap className="h-3 w-3" />
          Med
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 text-[11px] font-medium text-slate-400">
        Low
      </span>
    );
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-xs font-bold text-emerald-400">
          <Sparkles className="h-3 w-3" />
          {score}
        </span>
      );
    }
    if (score >= 60) {
      return (
        <span className="inline-flex items-center rounded-full bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 text-xs font-bold text-blue-400">
          {score}
        </span>
      );
    }
    if (score >= 40) {
      return (
        <span className="inline-flex items-center rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-xs font-bold text-amber-400">
          {score}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-400">
        {score}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="glass-panel overflow-hidden rounded-2xl p-6 text-center border border-slate-800">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <p className="mt-3 text-sm text-slate-400">Loading leads pipeline...</p>
        </div>
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="glass-panel overflow-hidden rounded-2xl p-8 text-center border border-slate-800">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-4">
          <Building2 className="h-7 w-7" />
        </div>
        <h3 className="text-base font-semibold text-white">No leads match filters</h3>
        <p className="mx-auto mt-1 max-w-sm text-sm text-slate-400">
          Try adjusting your search criteria, or add a new lead manually or seed demo prospects.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={onSeedDemo}
            className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-xs font-medium text-indigo-300 hover:bg-indigo-500/20 transition-all"
          >
            Seed 6 Demo Leads
          </button>
          <button
            onClick={onOpenCreate}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all shadow-md shadow-indigo-600/30"
          >
            + Add New Lead
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-panel overflow-hidden rounded-2xl border border-slate-800">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <tr>
              <th scope="col" className="px-5 py-3.5">Business & Industry</th>
              <th scope="col" className="px-4 py-3.5">Location</th>
              <th scope="col" className="px-4 py-3.5">Website</th>
              <th scope="col" className="px-3.5 py-3.5 text-center">Score</th>
              <th scope="col" className="px-3.5 py-3.5 text-center">Priority</th>
              <th scope="col" className="px-4 py-3.5">Pipeline Status</th>
              <th scope="col" className="px-4 py-3.5 text-center">AI Intelligence</th>
              <th scope="col" className="px-4 py-3.5 text-center">Quick Outreach</th>
              <th scope="col" className="px-4 py-3.5">Contacts</th>
              <th scope="col" className="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {leads.map((lead) => {
              const isAnalyzing = analyzingLeadId === lead.id;
              const hasAnalysis = Boolean(lead.score_reasons || lead.website_analysis);

              return (
                <tr
                  key={lead.id}
                  className="group transition-colors hover:bg-slate-900/40"
                >
                  {/* Business & Industry */}
                  <td className="px-5 py-4">
                    <div className="flex flex-col">
                      <span
                        onClick={() => onSelectLead(lead)}
                        className="cursor-pointer font-semibold text-white group-hover:text-indigo-300 transition-colors"
                      >
                        {lead.business_name}
                      </span>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="text-xs text-slate-400">{lead.industry || "General Business"}</span>
                        <span className="text-[10px] text-slate-600">•</span>
                        {lead.source === "Instagram Intent" ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-pink-500/10 border border-pink-500/30 px-2 py-0.5 text-[10px] font-bold text-pink-400">
                            <Instagram className="h-2.5 w-2.5" />
                            Instagram Intent
                          </span>
                        ) : lead.source === "google_maps" || lead.source === "Google Maps" ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                            <MapPin className="h-2.5 w-2.5" />
                            Google Maps
                          </span>
                        ) : (
                          <span className="text-[11px] text-slate-500 capitalize">{lead.source}</span>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Location */}
                  <td className="px-4 py-4 text-xs text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-500 flex-shrink-0" />
                      <span className="truncate max-w-[130px]">{lead.location || "Not specified"}</span>
                    </div>
                  </td>

                  {/* Website Status */}
                  <td className="px-4 py-4">
                    {!lead.has_website || !lead.website_url ? (
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-300">
                        <AlertCircle className="h-3 w-3" />
                        No Website
                      </span>
                    ) : (
                      <a
                        href={lead.website_url.startsWith("http") ? lead.website_url : `https://${lead.website_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 hover:underline"
                      >
                        <Globe className="h-3.5 w-3.5 flex-shrink-0" />
                        <span className="max-w-[120px] truncate">{lead.website_url.replace(/^https?:\/\//, "")}</span>
                        <ExternalLink className="h-3 w-3 opacity-70" />
                      </a>
                    )}
                  </td>

                  {/* Score */}
                  <td className="px-3.5 py-4 text-center">
                    {getScoreBadge(lead.lead_score)}
                  </td>

                  {/* Priority */}
                  <td className="px-3.5 py-4 text-center">
                    {getPriorityBadge(lead)}
                  </td>

                  {/* Pipeline Status */}
                  <td className="px-4 py-4">
                    {getStatusBadge(lead.status)}
                  </td>

                  {/* AI Intelligence Action */}
                  <td className="px-4 py-4 text-center">
                    {isAnalyzing ? (
                      <span className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600/30 border border-indigo-500/40 px-2.5 py-1 text-xs font-medium text-indigo-200 animate-pulse">
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                        <span>Analyzing...</span>
                      </span>
                    ) : !hasAnalysis && onAnalyzeLead ? (
                      <button
                        onClick={() => onAnalyzeLead(lead)}
                        className="inline-flex items-center gap-1 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-2.5 py-1 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 hover:opacity-90 active:scale-95 transition-all"
                      >
                        <Sparkles className="h-3 w-3" />
                        <span>Analyze with AI</span>
                      </button>
                    ) : lead.demo_url ? (
                      <button
                        onClick={() => onSelectLead(lead)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-xs text-emerald-400 hover:bg-emerald-500/20 font-semibold transition-colors"
                      >
                        <Layout className="h-3 w-3" />
                        <span>Demo Live</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => onSelectLead(lead)}
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        <span>AI Ready</span>
                      </button>
                    )}
                  </td>

                  {/* Quick Outreach */}
                  <td className="px-4 py-4 text-center">
                    {lead.source === "Instagram Intent" ? (
                      <button
                        onClick={(e) => handleTableInstagramClick(e, lead)}
                        title="1-Click IG DM (Copies tailored pitch & opens IG)"
                        className="inline-flex items-center gap-1.5 rounded-lg bg-pink-500/10 border border-pink-500/30 px-2.5 py-1 text-xs font-semibold text-pink-300 hover:bg-pink-500/20 active:scale-95 transition-all shadow-sm"
                      >
                        <Instagram className="h-3.5 w-3.5 text-pink-400" />
                        <span>IG DM</span>
                      </button>
                    ) : (lead.source === "google_maps" || lead.source === "Google Maps" || lead.phone) ? (
                      <button
                        onClick={(e) => handleTableWhatsAppClick(e, lead)}
                        title="1-Click WhatsApp Pitch with Live Demo Link"
                        className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 active:scale-95 transition-all shadow-sm"
                      >
                        <MessageSquare className="h-3.5 w-3.5 text-emerald-400" />
                        <span>WhatsApp</span>
                      </button>
                    ) : lead.email ? (
                      <a
                        href={`mailto:${lead.email}?subject=${encodeURIComponent(lead.outreach_email_subject || `Website for ${lead.business_name}`)}&body=${encodeURIComponent(lead.outreach_email_body || "")}`}
                        onClick={() => onQuickStatusUpdate && onQuickStatusUpdate(lead.id, "Pitch Sent")}
                        title="Send Cold Email"
                        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 px-2.5 py-1 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20 active:scale-95 transition-all"
                      >
                        <Mail className="h-3.5 w-3.5 text-indigo-400" />
                        <span>Email</span>
                      </a>
                    ) : (
                      <span className="text-xs text-slate-500">—</span>
                    )}
                  </td>

                  {/* Contacts */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1.5">
                      {lead.email && (
                        <a
                          href={`mailto:${lead.email}`}
                          title={lead.email}
                          className="rounded-lg bg-slate-800/80 p-1.5 text-slate-400 hover:bg-indigo-600 hover:text-white transition-colors"
                        >
                          <Mail className="h-3.5 w-3.5" />
                        </a>
                      )}
                      {lead.phone && (
                        <a
                          href={`tel:${lead.phone}`}
                          title={lead.phone}
                          className="rounded-lg bg-slate-800/80 p-1.5 text-slate-400 hover:bg-emerald-600 hover:text-white transition-colors"
                        >
                          <Phone className="h-3.5 w-3.5" />
                        </a>
                      )}
                      {lead.instagram_handle && (
                        <a
                          href={`https://instagram.com/${lead.instagram_handle.replace("@", "")}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={lead.instagram_handle}
                          className="rounded-lg bg-slate-800/80 p-1.5 text-slate-400 hover:bg-pink-600 hover:text-white transition-colors"
                        >
                          <Instagram className="h-3.5 w-3.5" />
                        </a>
                      )}
                      {!lead.email && !lead.phone && !lead.instagram_handle && (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => onSelectLead(lead)}
                        title="View Details & Drawer"
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onEditLead(lead)}
                        title="Edit Lead"
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteLead(lead)}
                        title="Delete Lead"
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-950/60 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
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
