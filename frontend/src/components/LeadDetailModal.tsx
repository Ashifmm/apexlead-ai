"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Globe,
  ExternalLink,
  Mail,
  Phone,
  Instagram,
  Sparkles,
  Copy,
  Check,
  Building2,
  MapPin,
  Flame,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Send,
  Loader2,
  ShieldCheck,
  Smartphone,
  MousePointerClick,
  Layers,
  Save,
  Layout,
  Monitor,
  Tablet,
  RefreshCw,
  Code2,
  Download,
  Palette,
  CheckCircle,
  FileCode,
  MessageSquare,
} from "lucide-react";
import { Lead, WebsiteAuditResult } from "@/types/lead";
import { getLeadPriority } from "./LeadTable";
import { fetchDemoDetails } from "@/lib/api";

interface LeadDetailModalProps {
  lead: Lead | null;
  isOpen?: boolean;
  onClose: () => void;
  onUpdateStatus: (id: number, newStatus: string) => void;
  onSaveOutreachDrafts?: (
    id: number,
    data: {
      outreach_email_subject?: string;
      outreach_email_body?: string;
      outreach_instagram_dm?: string;
      status?: string;
    }
  ) => Promise<void>;
  onRunLeadAnalysis?: (lead: Lead) => Promise<void>;
  onRunWebsiteAudit?: (lead: Lead) => Promise<void>;
  onGenerateDemo?: (
    lead: Lead,
    options?: { custom_instructions?: string; theme_color?: string }
  ) => Promise<void>;
  isAnalyzingLead?: boolean;
  isAuditingWebsite?: boolean;
  isGeneratingDemo?: boolean;
}

export const LeadDetailModal: React.FC<LeadDetailModalProps> = ({
  lead,
  isOpen = true,
  onClose,
  onUpdateStatus,
  onSaveOutreachDrafts,
  onRunLeadAnalysis,
  onRunWebsiteAudit,
  onGenerateDemo,
  isAnalyzingLead = false,
  isAuditingWebsite = false,
  isGeneratingDemo = false,
}) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "lead_ai" | "website_audit" | "outreach" | "website_demo">("overview");

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

  // Phase 6 Demo Generator state
  const [demoPage, setDemoPage] = useState<"index.html" | "about.html" | "services.html" | "contact.html">("index.html");
  const [deviceViewport, setDeviceViewport] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [customInstructions, setCustomInstructions] = useState<string>("");
  const [selectedTheme, setSelectedTheme] = useState<string>("auto");
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [showHtmlCode, setShowHtmlCode] = useState<boolean>(false);
  const [activeCodePage, setActiveCodePage] = useState<string>("index.html");
  const [copiedDemoLink, setCopiedDemoLink] = useState<boolean>(false);
  const [copiedCodeToast, setCopiedCodeToast] = useState<boolean>(false);
  const [demoPagesData, setDemoPagesData] = useState<Record<string, string>>({});
  const [isLoadingDemoPages, setIsLoadingDemoPages] = useState<boolean>(false);

  // Fetch demo pages from API whenever demo tab is opened or lead changes
  useEffect(() => {
    if (lead && (lead.demo_url || lead.demo_preview_html) && activeTab === "website_demo") {
      setIsLoadingDemoPages(true);
      fetchDemoDetails(lead.id)
        .then((res) => {
          if (res && res.pages && Object.keys(res.pages).length > 0) {
            setDemoPagesData(res.pages);
          } else if (lead.demo_preview_html) {
            setDemoPagesData({ "index.html": lead.demo_preview_html });
          }
        })
        .catch((err) => {
          console.error("Failed to load demo pages:", err);
          if (lead.demo_preview_html) {
            setDemoPagesData({ "index.html": lead.demo_preview_html });
          }
        })
        .finally(() => {
          setIsLoadingDemoPages(false);
        });
    }
  }, [lead?.id, lead?.demo_url, lead?.demo_preview_html, activeTab]);

  const handleTriggerGenerateDemo = async () => {
    if (!onGenerateDemo || !lead) return;
    try {
      await onGenerateDemo(lead, {
        custom_instructions: customInstructions.trim() || undefined,
        theme_color: selectedTheme !== "auto" ? selectedTheme : undefined,
      });
      setIframeKey((prev) => prev + 1);
    } catch (err) {
      console.error("Failed to generate demo:", err);
    }
  };


  // Editable drafts state
  const [emailSubject, setEmailSubject] = useState<string>("");
  const [emailBody, setEmailBody] = useState<string>("");
  const [instagramDm, setInstagramDm] = useState<string>("");
  const [isSavingDrafts, setIsSavingDrafts] = useState<boolean>(false);
  const [draftSavedToast, setDraftSavedToast] = useState<boolean>(false);

  // Sync state whenever lead changes
  useEffect(() => {
    if (lead) {
      setEmailSubject(lead.outreach_email_subject || "");
      setEmailBody(lead.outreach_email_body || "");
      setInstagramDm(lead.outreach_instagram_dm || "");
    }
  }, [lead]);

  if (!lead || !isOpen) return null;

  const copyToClipboard = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleSaveDrafts = async (newStatus?: string) => {
    if (!onSaveOutreachDrafts) return;
    setIsSavingDrafts(true);
    try {
      await onSaveOutreachDrafts(lead.id, {
        outreach_email_subject: emailSubject,
        outreach_email_body: emailBody,
        outreach_instagram_dm: instagramDm,
        status: newStatus || lead.status,
      });
      setDraftSavedToast(true);
      setTimeout(() => setDraftSavedToast(false), 3000);
    } catch (err) {
      console.error("Failed to save drafts:", err);
    } finally {
      setIsSavingDrafts(false);
    }
  };

  const handleSendColdEmail = () => {
    const to = lead.email ? encodeURIComponent(lead.email) : "";
    const subj = encodeURIComponent(emailSubject || `Quick question regarding ${lead.business_name}'s web presence`);
    const body = encodeURIComponent(emailBody || "");
    const mailtoUrl = `mailto:${to}?subject=${subj}&body=${body}`;
    window.location.href = mailtoUrl;
  };

  const handleOpenInstagramDm = () => {
    const handle = (lead.instagram_handle || "").replace("@", "").trim();
    const pitch = instagramDm || (lead.outreach_instagram_dm || `Hey team ${lead.business_name}! Love your work...`);
    navigator.clipboard.writeText(pitch);
    setCopiedField("ig_dm");
    setTimeout(() => setCopiedField(null), 3000);
    const targetUrl = handle ? `https://ig.me/m/${handle}` : "https://ig.me/m/";
    window.open(targetUrl, "_blank", "noopener,noreferrer");
  };

  const getFormattedWhatsAppPitch = (currentLead: Lead) => {
    // If currentLead already has structured pitch with Google Maps compliment, reuse it
    if (
      currentLead.outreach_instagram_dm &&
      currentLead.outreach_instagram_dm.startsWith("Hey ") &&
      currentLead.outreach_instagram_dm.includes("★ reviews on Google Maps")
    ) {
      return currentLead.outreach_instagram_dm;
    }

    // Rating from notes or high score
    const ratingMatch = (currentLead.notes || "").match(/(\d+\.\d+)★/);
    const rating = ratingMatch ? ratingMatch[1] : (currentLead.lead_score >= 90 ? "4.8" : "4.6");

    // City & Niche
    let city = "your city";
    if (currentLead.location) {
      const parts = currentLead.location.split(",");
      city = parts[parts.length - 1].trim();
    }
    const niche = currentLead.industry || "your industry";
    const demoUrl = currentLead.demo_url || `http://localhost:8000/demos/${currentLead.id}/`;

    return (
      `Hey ${currentLead.business_name}, noticed your stellar ${rating}★ reviews on Google Maps!\n\n` +
      `Local customers in ${city} are searching for ${niche}, but couldn't find your official website.\n\n` +
      `We crafted a modern, responsive showcase preview for you: ${demoUrl}\n\n` +
      `Take a 30-second look. Open to feedback!`
    );
  };

  const handleSendWhatsAppPitch = () => {
    const digits = (lead.phone || "").replace(/\D/g, "");
    const waPhone = digits.length === 10 ? `91${digits}` : digits || "919811001122";
    const pitchText = getFormattedWhatsAppPitch(lead);
    const waUrl = `https://api.whatsapp.com/send?phone=${waPhone}&text=${encodeURIComponent(pitchText)}`;
    window.open(waUrl, "_blank", "noopener,noreferrer");
    // Auto-update lead status to "Pitch Sent"
    onUpdateStatus(lead.id, "Pitch Sent");
  };

  const handleCopyPitchAndDemo = () => {
    const pitchText = getFormattedWhatsAppPitch(lead);
    navigator.clipboard.writeText(pitchText);
    setCopiedField("pitch_demo");
    setTimeout(() => setCopiedField(null), 3000);
  };

  const priority = getLeadPriority(lead);


  // Helper to parse website audit text into scores if available
  const parseAuditScores = () => {
    const text = lead.website_analysis || "";
    const overallMatch = text.match(/Overall:\s*(\d+)\/100/i);
    const designMatch = text.match(/Design:\s*(\d+)/i);
    const mobileMatch = text.match(/Mobile:\s*(\d+)/i);
    const conversionMatch = text.match(/Conversion:\s*(\d+)/i);

    if (overallMatch) {
      return {
        overall: parseInt(overallMatch[1], 10),
        design: designMatch ? parseInt(designMatch[1], 10) : 50,
        mobile: mobileMatch ? parseInt(mobileMatch[1], 10) : 50,
        conversion: conversionMatch ? parseInt(conversionMatch[1], 10) : 50,
      };
    }
    return null;
  };

  const auditScores = parseAuditScores();

  // Status steps for the outreach tracker
  const stages = [
    { id: "Outreach Ready", label: "Outreach Ready", legacyIds: ["new", "analyzed", "scored", "outreach_generated", "demo_generated"] },
    { id: "Pitch Sent", label: "Pitch Sent", legacyIds: ["contacted"] },
    { id: "In Discussion", label: "In Discussion", legacyIds: [] },
    { id: "Deal Won", label: "Deal Won 🎉", legacyIds: ["converted"] },
    { id: "Not Interested", label: "Not Interested", legacyIds: ["rejected"] },
  ];

  const currentStageIndex = stages.findIndex(
    (s) => s.id.toLowerCase() === (lead.status || "").toLowerCase() || s.legacyIds.includes(lead.status)
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="lead-modal-title"
    >
      {/* Backdrop Overlay */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity cursor-pointer"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        aria-hidden="true"
        data-testid="lead-drawer-backdrop"
      />

      {/* Modal Container */}
      <div
        className="relative z-10 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-6 py-4 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="lead-modal-title" className="text-lg font-bold text-white tracking-tight">{lead.business_name}</h2>
                <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-400">
                  #{lead.id}
                </span>
                {priority === "high" && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/15 border border-rose-500/30 px-2.5 py-0.5 text-xs font-bold text-rose-400">
                    <Flame className="h-3.5 w-3.5" /> High Opportunity
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {lead.industry || "General Industry"} • {lead.location || "Location not specified"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Quick Status Select */}
            <select
              value={lead.status}
              onChange={(e) => onUpdateStatus(lead.id, e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="Outreach Ready">Status: Outreach Ready</option>
              <option value="Pitch Sent">Status: Pitch Sent</option>
              <option value="In Discussion">Status: In Discussion</option>
              <option value="Deal Won">Status: Deal Won 🎉</option>
              <option value="Closed">Status: Closed</option>
              <option value="Not Interested">Status: Not Interested</option>
              <option value="new">Status: New</option>
              <option value="analyzed">Status: Analyzed</option>
              <option value="scored">Status: Scored</option>
              <option value="outreach_generated">Status: Outreach Generated</option>
              <option value="demo_generated">Status: Demo Ready</option>
              <option value="contacted">Status: Contacted</option>
              <option value="converted">Status: Converted</option>
              <option value="rejected">Status: Rejected</option>
            </select>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              aria-label="Close drawer"
              data-testid="lead-drawer-close-btn"
              className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/20 px-6 text-xs font-medium text-slate-400 overflow-x-auto">
          <button
            onClick={() => setActiveTab("overview")}
            className={`border-b-2 py-3 px-3.5 whitespace-nowrap transition-colors ${
              activeTab === "overview"
                ? "border-indigo-500 text-indigo-400 font-semibold"
                : "border-transparent hover:text-slate-200"
            }`}
          >
            Overview & Context
          </button>
          <button
            onClick={() => setActiveTab("lead_ai")}
            className={`border-b-2 py-3 px-3.5 whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "lead_ai"
                ? "border-indigo-500 text-indigo-400 font-semibold"
                : "border-transparent hover:text-slate-200"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>AI Lead Intelligence</span>
            {lead.lead_score > 0 && (
              <span className="rounded-full bg-indigo-500/20 px-1.5 py-0.2 text-[10px] text-indigo-300">
                {lead.lead_score}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("website_audit")}
            className={`border-b-2 py-3 px-3.5 whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "website_audit"
                ? "border-indigo-500 text-indigo-400 font-semibold"
                : "border-transparent hover:text-slate-200"
            }`}
          >
            <Globe className="h-3.5 w-3.5 text-cyan-400" />
            <span>Website Audit</span>
            {lead.has_website && (
              <span className="rounded-full bg-cyan-500/20 px-1.5 py-0.2 text-[10px] text-cyan-300">Live</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("outreach")}
            className={`border-b-2 py-3 px-3.5 whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "outreach"
                ? "border-indigo-500 text-indigo-400 font-semibold"
                : "border-transparent hover:text-slate-200"
            }`}
          >
            <Mail className="h-3.5 w-3.5 text-purple-400" />
            <span>Outreach Studio</span>
            {lead.outreach_email_body && (
              <span className="rounded-full bg-purple-500/20 px-1.5 py-0.2 text-[10px] text-purple-300">Drafted</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("website_demo")}
            className={`border-b-2 py-3 px-3.5 whitespace-nowrap transition-colors flex items-center gap-1.5 ${
              activeTab === "website_demo"
                ? "border-emerald-500 text-emerald-400 font-semibold"
                : "border-transparent hover:text-slate-200"
            }`}
          >
            <Layout className="h-3.5 w-3.5 text-emerald-400" />
            <span>Website Demo</span>
            {lead.demo_url ? (
              <span className="rounded-full bg-emerald-500/20 px-1.5 py-0.2 text-[10px] text-emerald-300 font-bold">
                Ready
              </span>
            ) : (
              <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400">
                Phase 6
              </span>
            )}
          </button>
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* TAB 1: OVERVIEW & CONTEXT */}
          {activeTab === "overview" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Online Presence */}
                <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4 space-y-3">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                    Online Presence & Origin
                  </h4>
                  <div className="text-sm">
                    <span className="text-slate-500 text-xs">Website URL:</span>
                    <div className="mt-1">
                      {lead.website_url ? (
                        <a
                          href={lead.website_url.startsWith("http") ? lead.website_url : `https://${lead.website_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 font-medium hover:underline"
                        >
                          <Globe className="h-4 w-4" />
                          <span>{lead.website_url}</span>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-300">
                          <AlertTriangle className="h-3.5 w-3.5" /> No Website on File (Prime Pitch Target)
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="text-slate-500 text-xs">Acquisition Source:</span>
                    <p className="capitalize text-slate-300 mt-0.5 font-medium">{lead.source}</p>
                  </div>
                </div>

                {/* Direct Contacts */}
                <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4 space-y-3">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                    Contact Channels
                  </h4>
                  <div className="text-sm">
                    <span className="text-slate-500 text-xs">Email:</span>
                    <p className="text-slate-200 mt-0.5">
                      {lead.email ? (
                        <a href={`mailto:${lead.email}`} className="text-indigo-400 hover:underline">
                          {lead.email}
                        </a>
                      ) : (
                        <span className="text-slate-500">Not recorded</span>
                      )}
                    </p>
                  </div>
                  <div className="text-sm">
                    <span className="text-slate-500 text-xs">Phone:</span>
                    <p className="text-slate-200 mt-0.5">
                      {lead.phone ? (
                        <a href={`tel:${lead.phone}`} className="text-emerald-400 hover:underline">
                          {lead.phone}
                        </a>
                      ) : (
                        <span className="text-slate-500">Not recorded</span>
                      )}
                    </p>
                  </div>
                  <div className="text-sm">
                    <span className="text-slate-500 text-xs">Instagram:</span>
                    <p className="text-slate-200 mt-0.5">
                      {lead.instagram_handle ? (
                        <a
                          href={`https://instagram.com/${lead.instagram_handle.replace("@", "")}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-pink-400 hover:underline font-medium"
                        >
                          {lead.instagram_handle}
                        </a>
                      ) : (
                        <span className="text-slate-500">Not recorded</span>
                      )}
                    </p>
                  </div>

                  {/* Direct Outreach Dispatch Buttons */}
                  <div className="pt-2.5 border-t border-slate-800/80 flex flex-col sm:flex-row flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleSendColdEmail}
                      className="flex-1 min-w-[120px] flex items-center justify-center gap-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 text-xs font-semibold shadow-md shadow-purple-600/20 active:scale-95 transition-all"
                      title="Launch pre-filled cold email"
                    >
                      <Mail className="h-3.5 w-3.5" />
                      <span>Send Cold Email</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleSendWhatsAppPitch}
                      className="flex-1 min-w-[130px] flex items-center justify-center gap-1.5 rounded-xl bg-[#25D366] hover:bg-[#20ba59] text-white px-3 py-2 text-xs font-semibold shadow-md shadow-emerald-500/20 active:scale-95 transition-all"
                      title="Launch pre-filled WhatsApp pitch with custom demo link and mark Pitch Sent"
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      <span>WhatsApp Pitch</span>
                    </button>
                    {(lead.source === "google_maps" || lead.demo_url) && (
                      <button
                        type="button"
                        onClick={handleCopyPitchAndDemo}
                        className="flex-1 min-w-[140px] flex items-center justify-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-950/40 hover:bg-emerald-900/40 text-emerald-300 px-3 py-2 text-xs font-semibold active:scale-95 transition-all"
                        title="Copy structured pitch and live demo link to clipboard"
                      >
                        {copiedField === "pitch_demo" ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                            <span>Copied Pitch!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5" />
                            <span>Copy Pitch & Demo</span>
                          </>
                        )}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleOpenInstagramDm}
                      className="flex-1 min-w-[130px] flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 hover:opacity-90 text-white px-3 py-2 text-xs font-semibold shadow-md shadow-pink-600/20 active:scale-95 transition-all"
                      title="Copies pitch to clipboard and opens Instagram DM"
                    >
                      <Instagram className="h-3.5 w-3.5" />
                      <span>{copiedField === "ig_dm" ? "Copied & Opened!" : "Open Instagram DM"}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* FOR MAPS LEADS: Live Iframe Preview + Send WhatsApp Pitch with Demo */}
              {(lead.source === "google_maps" || lead.demo_url) && (
                <div className="rounded-2xl border border-emerald-500/30 bg-slate-950/60 p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                        Live Ultra-Premium Website Demo Preview
                      </h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleCopyPitchAndDemo}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-950/50 hover:bg-emerald-900/50 text-emerald-300 px-3 py-1.5 text-xs font-semibold active:scale-95 transition-all"
                        title="Copy structured pitch and live demo link"
                      >
                        {copiedField === "pitch_demo" ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                            <span>Pitch Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5" />
                            <span>Copy Pitch & Demo Link</span>
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={handleSendWhatsAppPitch}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-[#25D366] hover:bg-[#20ba59] text-white px-3 py-1.5 text-xs font-bold shadow-md shadow-emerald-600/20 active:scale-95 transition-all"
                        title="Open WhatsApp with pre-filled pitch and mark Pitch Sent"
                      >
                        <MessageSquare className="h-3.5 w-3.5" />
                        <span>Send WhatsApp Pitch with Demo</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => window.open(lead.demo_url || `http://localhost:8000/demos/${lead.id}/`, "_blank")}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:text-white transition-all"
                        title="Test In New Tab"
                      >
                        <ExternalLink className="h-3.5 w-3.5 text-emerald-400" />
                        <span>Test In New Tab</span>
                      </button>
                      <a
                        href={lead.demo_url || `http://localhost:8000/demos/${lead.id}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-xl border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white"
                        title="Open live hosted demo"
                      >
                        <span>Open Live</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                  <div className="relative w-full h-80 rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-inner">
                    <iframe
                      src={lead.demo_url || `http://localhost:8000/demos/${lead.id}/`}
                      title={`Demo preview for ${lead.business_name}`}
                      className="w-full h-full border-0 bg-white"
                    />
                  </div>
                </div>
              )}

              {/* FOR INSTAGRAM LEADS: Queue Status + Intent Quote & Bio */}
              {lead.source === "Instagram Intent" && (
                <div className="rounded-2xl border border-pink-500/30 bg-slate-950/60 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Instagram className="h-4 w-4 text-pink-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-pink-400">
                        Instagram Intent Lead
                      </h4>
                    </div>
                    <div>
                      {lead.status === "contacted" ? (
                        <span className="rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-bold">
                          Auto-DM Queue Status: Dispatched ✓
                        </span>
                      ) : (
                        <span className="rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/30 px-2.5 py-0.5 text-xs font-bold">
                          Auto-DM Queue Status: Pending ⏳
                        </span>
                      )}
                    </div>
                  </div>

                  {lead.notes && (
                    <div className="rounded-xl bg-slate-900/90 border border-slate-800/80 p-3.5 text-xs text-slate-200">
                      <span className="text-[11px] font-bold text-pink-400 block mb-1">
                        Captured User Intent & Profile Bio:
                      </span>
                      <p className="whitespace-pre-wrap leading-relaxed">{lead.notes}</p>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
                    <span className="text-[11px] text-slate-400">
                      Rule: Demo generation bypassed for social leads to prevent spam.
                    </span>
                    <button
                      type="button"
                      onClick={handleOpenInstagramDm}
                      className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 hover:opacity-90 text-white px-3.5 py-1.5 text-xs font-semibold shadow-md active:scale-95 transition-all"
                    >
                      <Instagram className="h-3.5 w-3.5" />
                      <span>{copiedField === "ig_dm" ? "Copied & Opened!" : "Open Instagram DM"}</span>
                    </button>
                  </div>
                </div>
              )}

              {lead.notes && lead.source !== "Instagram Intent" && (
                <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-1">
                    Agency Notes
                  </h4>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{lead.notes}</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: AI LEAD INTELLIGENCE */}
          {activeTab === "lead_ai" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">Gemini Opportunity Evaluation</h3>
                    {priority === "high" ? (
                      <span className="rounded-full bg-rose-500/20 border border-rose-500/30 px-2 py-0.5 text-xs font-bold text-rose-300">
                        Priority: High
                      </span>
                    ) : priority === "medium" ? (
                      <span className="rounded-full bg-amber-500/20 border border-amber-500/30 px-2 py-0.5 text-xs font-bold text-amber-300">
                        Priority: Medium
                      </span>
                    ) : (
                      <span className="rounded-full bg-slate-800 border border-slate-700 px-2 py-0.5 text-xs font-medium text-slate-400">
                        Priority: Low
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Evaluated from public profile, online gap analysis, and sales readiness.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 px-3.5 py-1.5 text-xl font-bold text-indigo-400">
                    <Sparkles className="h-5 w-5" />
                    <span>{lead.lead_score} / 100</span>
                  </div>

                  {onRunLeadAnalysis && (
                    <button
                      onClick={() => onRunLeadAnalysis(lead)}
                      disabled={isAnalyzingLead}
                      className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-3 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                    >
                      {isAnalyzingLead ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4" />
                          <span>{lead.score_reasons ? "Re-evaluate Lead" : "Evaluate with AI"}</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Score Reasons & Pain Points */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
                <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                  Analysis & Identified Pain Points
                </h4>
                {lead.score_reasons ? (
                  <div className="rounded-xl bg-slate-900/80 p-4 border border-slate-800/80 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                    {lead.score_reasons}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-800 p-6 text-center text-xs text-slate-400">
                    <p className="text-slate-300 font-medium">No Lead Evaluation Recorded Yet</p>
                    <p className="mt-1 max-w-sm mx-auto">
                      Click the "Evaluate with AI" button above to run Gemini scoring and extract business pain points.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: WEBSITE AUDIT */}
          {activeTab === "website_audit" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
                <div>
                  <h3 className="text-base font-bold text-white">Live Website Technical & UX Audit</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Factual DOM crawling: mobile responsiveness, headings, CTAs, and modern design metrics.
                  </p>
                </div>

                {onRunWebsiteAudit && (
                  <button
                    onClick={() => onRunWebsiteAudit(lead)}
                    disabled={isAuditingWebsite || !lead.website_url}
                    className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 px-3.5 py-2 text-xs font-semibold text-white shadow-md shadow-cyan-500/20 hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                  >
                    {isAuditingWebsite ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Auditing Site...</span>
                      </>
                    ) : (
                      <>
                        <Globe className="h-4 w-4" />
                        <span>{lead.website_analysis ? "Re-crawl Website" : "Run Website Audit"}</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Audit Scores Meters if parsed */}
              {auditScores && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-center">
                    <span className="text-[11px] font-semibold uppercase text-slate-400">Overall Health</span>
                    <p className="text-2xl font-bold text-indigo-400 mt-1">{auditScores.overall}/100</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-center">
                    <span className="text-[11px] font-semibold uppercase text-slate-400">Design & UI</span>
                    <p className="text-2xl font-bold text-cyan-400 mt-1">{auditScores.design}/100</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-center">
                    <span className="text-[11px] font-semibold uppercase text-slate-400">Mobile Ready</span>
                    <p className="text-2xl font-bold text-emerald-400 mt-1">{auditScores.mobile}/100</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-center">
                    <span className="text-[11px] font-semibold uppercase text-slate-400">Conversion / CTA</span>
                    <p className="text-2xl font-bold text-amber-400 mt-1">{auditScores.conversion}/100</p>
                  </div>
                </div>
              )}

              {/* Full Audit Report */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
                <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                  Audit Findings & Recommendations
                </h4>
                {lead.website_analysis ? (
                  <div className="rounded-xl bg-slate-900/80 p-4 border border-slate-800/80 text-xs sm:text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                    {lead.website_analysis}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-800 p-8 text-center text-xs text-slate-400">
                    <Globe className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-300 font-medium">No Website Audit Report Available</p>
                    <p className="mt-1 max-w-sm mx-auto">
                      {lead.website_url
                        ? "Click 'Run Website Audit' above to test mobile viewport tags, CTAs, headings, and SSL security."
                        : "This lead does not have a website URL. Consider pitching a brand-new website build!"}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: OUTREACH STUDIO */}
          {activeTab === "outreach" && (
            <div className="space-y-5">
              {/* Outreach Pipeline Tracker */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Outreach Stage Tracker
                </span>
                <div className="mt-2.5 flex items-center justify-between gap-1 overflow-x-auto">
                  {stages.map((stg, idx) => {
                    const isPassed = currentStageIndex >= idx;
                    const isCurrent = currentStageIndex === idx;

                    return (
                      <button
                        key={stg.id}
                        onClick={() => onUpdateStatus(lead.id, stg.id)}
                        className={`flex-1 min-w-[110px] text-center py-2 px-2 rounded-xl text-xs font-medium transition-all ${
                          isCurrent
                            ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                            : isPassed
                            ? "bg-indigo-950/60 text-indigo-300 border border-indigo-800/50"
                            : "bg-slate-900/60 text-slate-500 border border-slate-800/60 hover:text-slate-300"
                        }`}
                      >
                        {stg.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Cold Email Draft */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-purple-400" />
                    <h4 className="text-sm font-semibold text-white">Cold Email Proposal Draft</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleSendColdEmail}
                      className="flex items-center gap-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 text-xs font-semibold shadow-md shadow-purple-600/20 active:scale-95 transition-all"
                      title="Launch pre-filled cold email"
                    >
                      <Mail className="h-3.5 w-3.5" />
                      <span>Send Cold Email</span>
                    </button>
                    <button
                      onClick={() => copyToClipboard(`Subject: ${emailSubject}\n\n${emailBody}`, "email")}
                      className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:text-white transition-colors"
                    >
                      {copiedField === "email" ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                          <span className="text-emerald-400 font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          <span>Copy Full Email</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Editable Subject */}
                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Subject Line
                  </label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    placeholder="Enter email subject line..."
                    className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-purple-500/70 focus:ring-2 focus:ring-purple-500/20"
                  />
                </div>

                {/* Editable Body */}
                <div>
                  <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Email Body
                  </label>
                  <textarea
                    rows={7}
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    placeholder="No cold email generated yet. Run AI Lead Analysis to draft a tailored pitch."
                    className="w-full rounded-xl border border-slate-800 bg-slate-900 p-3.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-purple-500/70 focus:ring-2 focus:ring-purple-500/20 font-sans leading-relaxed"
                  />
                </div>
              </div>

              {/* Instagram DM Draft */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Instagram className="h-4 w-4 text-pink-400" />
                    <h4 className="text-sm font-semibold text-white">Instagram DM Draft</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500">{instagramDm.length} chars</span>
                    <button
                      type="button"
                      onClick={handleOpenInstagramDm}
                      className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-pink-600 via-rose-600 to-amber-500 hover:opacity-90 text-white px-3 py-1.5 text-xs font-semibold shadow-md shadow-pink-600/20 active:scale-95 transition-all"
                      title="Copies pitch to clipboard and opens Instagram DM"
                    >
                      <Instagram className="h-3.5 w-3.5" />
                      <span>{copiedField === "ig_dm" ? "Copied & Opened!" : "Open Instagram DM"}</span>
                    </button>
                    <button
                      onClick={() => copyToClipboard(instagramDm, "dm")}
                      className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:text-white transition-colors"
                    >
                      {copiedField === "dm" ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                          <span className="text-emerald-400 font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          <span>Copy DM</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <textarea
                  rows={4}
                  value={instagramDm}
                  onChange={(e) => setInstagramDm(e.target.value)}
                  placeholder="No Instagram DM generated yet. Run AI Lead Analysis to draft a direct social pitch."
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 p-3.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-pink-500/70 focus:ring-2 focus:ring-pink-500/20 leading-relaxed"
                />
              </div>

              {/* Outreach Action Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2">
                  {draftSavedToast && (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-medium animate-in fade-in">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Draft changes saved!
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => handleSaveDrafts()}
                    disabled={isSavingDrafts}
                    className="flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 active:scale-95 disabled:opacity-50 transition-all"
                  >
                    {isSavingDrafts ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                    <span>Save Drafts</span>
                  </button>

                  <button
                    onClick={() => handleSaveDrafts("contacted")}
                    disabled={isSavingDrafts}
                    className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-emerald-600/30 hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>Save & Mark Contacted</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: WEBSITE DEMO GENERATOR (PHASE 6) */}
          {activeTab === "website_demo" && (() => {
            const rawBaseUrl = lead.demo_url || `http://localhost:8000/demos/${lead.id}/`;
            const baseDemoUrl = rawBaseUrl.endsWith("/") ? rawBaseUrl : `${rawBaseUrl}/`;
            const currentPreviewUrl = `${baseDemoUrl}${demoPage === "index.html" ? "" : demoPage}`;
            const hasDemo = Boolean(lead.demo_url || lead.demo_preview_html || Object.keys(demoPagesData).length > 0);
            const activePageCode = demoPagesData[activeCodePage] || (activeCodePage === "index.html" ? lead.demo_preview_html : "") || "";

            return (
              <div className="space-y-5">
                {/* Generation & Customization Control Card */}
                <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                          <Layout className="h-5 w-5 text-emerald-400" />
                          <span>Multi-Page Interactive Website Prototype</span>
                        </h3>
                        {hasDemo ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-bold text-emerald-400">
                            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                            Demo Ready
                          </span>
                        ) : (
                          <span className="rounded-full bg-slate-800 border border-slate-700 px-2.5 py-0.5 text-xs font-medium text-slate-400">
                            Phase 6 Generator
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        Bespoke multi-page Tailwind CSS prototype with working navigation: Home, About, Services, and Contact.
                      </p>
                    </div>

                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={handleTriggerGenerateDemo}
                        disabled={isGeneratingDemo}
                        className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-emerald-600/20 hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                      >
                        {isGeneratingDemo ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Building Multi-Page Prototype...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            <span>{hasDemo ? "Re-generate Demo" : "Generate Multi-Page Demo"}</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Customization Inputs */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2 border-t border-slate-800/80">
                    <div className="md:col-span-8">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Optional Agency Guidance / Prompts
                      </label>
                      <input
                        type="text"
                        value={customInstructions}
                        onChange={(e) => setCustomInstructions(e.target.value)}
                        placeholder="e.g. Highlight 24/7 emergency service, 15% spring discount, focus on residential..."
                        className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/20"
                      />
                    </div>
                    <div className="md:col-span-4">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Theme Palette
                      </label>
                      <select
                        value={selectedTheme}
                        onChange={(e) => setSelectedTheme(e.target.value)}
                        className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-200 outline-none focus:border-emerald-500/70 cursor-pointer"
                      >
                        <option value="auto">Auto (Match Industry: {lead.industry || 'General'})</option>
                        <option value="indigo">Modern Indigo (Tech & Agency)</option>
                        <option value="amber">Industrial Amber (Roofing & Construction)</option>
                        <option value="emerald">Emerald Growth (Wealth & Home Care)</option>
                        <option value="cyan">Medical & Wellness Cyan (Dental & Clinic)</option>
                        <option value="rose">Electric Rose (Auto Detailing & Beauty)</option>
                        <option value="slate">Executive Slate (Corporate & Legal)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* If Demo exists: Device controls, page tabs, iframe & code preview */}
                {hasDemo ? (
                  <div className="space-y-4">
                    {/* Viewport & Navigation Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-950/40 p-3">
                      {/* Page Switcher */}
                      <div className="flex items-center gap-1 overflow-x-auto text-xs">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-2 hidden sm:inline">
                          Pages:
                        </span>
                        {[
                          { id: "index.html", label: "🏠 Home" },
                          { id: "about.html", label: "ℹ️ About" },
                          { id: "services.html", label: "🛠️ Services" },
                          { id: "contact.html", label: "✉️ Contact" },
                        ].map((p) => (
                          <button
                            key={p.id}
                            onClick={() => setDemoPage(p.id as any)}
                            className={`px-3 py-1.5 rounded-xl font-semibold text-xs transition-all ${
                              demoPage === p.id
                                ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                            }`}
                          >
                            {p.label}
                          </button>
                        ))}
                      </div>

                      {/* Viewport Devices */}
                      <div className="flex items-center gap-2">
                        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5">
                          <button
                            onClick={() => setDeviceViewport("desktop")}
                            title="Desktop View (100%)"
                            className={`p-1.5 rounded-lg text-xs transition-colors ${
                              deviceViewport === "desktop"
                                ? "bg-slate-800 text-white"
                                : "text-slate-400 hover:text-white"
                            }`}
                          >
                            <Monitor className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setDeviceViewport("tablet")}
                            title="Tablet View (768px)"
                            className={`p-1.5 rounded-lg text-xs transition-colors ${
                              deviceViewport === "tablet"
                                ? "bg-slate-800 text-white"
                                : "text-slate-400 hover:text-white"
                            }`}
                          >
                            <Tablet className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setDeviceViewport("mobile")}
                            title="Mobile View (390px)"
                            className={`p-1.5 rounded-lg text-xs transition-colors ${
                              deviceViewport === "mobile"
                                ? "bg-slate-800 text-white"
                                : "text-slate-400 hover:text-white"
                            }`}
                          >
                            <Smartphone className="h-4 w-4" />
                          </button>
                        </div>

                        {/* Secondary Actions */}
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(currentPreviewUrl);
                            setCopiedDemoLink(true);
                            setTimeout(() => setCopiedDemoLink(false), 2000);
                          }}
                          title="Copy Hosted Demo Link"
                          className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 hover:text-white transition-colors"
                        >
                          {copiedDemoLink ? (
                            <>
                              <Check className="h-3.5 w-3.5 text-emerald-400" />
                              <span className="text-emerald-400 font-semibold">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5" />
                              <span>Copy Link</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => setShowHtmlCode(!showHtmlCode)}
                          className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                            showHtmlCode
                              ? "border-emerald-500 bg-emerald-950/40 text-emerald-300"
                              : "border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          <Code2 className="h-3.5 w-3.5" />
                          <span>{showHtmlCode ? "Hide HTML" : "View Code"}</span>
                        </button>

                        <a
                          href={currentPreviewUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-400 transition-colors"
                        >
                          <span>Open Live</span>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </div>
                    </div>

                    {/* Raw HTML Code Viewer Drawer (Toggleable) */}
                    {showHtmlCode && (
                      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-3 animate-in fade-in">
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-1">
                            {["index.html", "about.html", "services.html", "contact.html"].map((fn) => (
                              <button
                                key={fn}
                                onClick={() => setActiveCodePage(fn)}
                                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-colors ${
                                  activeCodePage === fn
                                    ? "bg-emerald-600 text-white font-bold"
                                    : "bg-slate-900 text-slate-400 hover:text-slate-200"
                                }`}
                              >
                                {fn}
                              </button>
                            ))}
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-mono text-slate-500">
                              {activePageCode.length} bytes
                            </span>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(activePageCode);
                                setCopiedCodeToast(true);
                                setTimeout(() => setCopiedCodeToast(false), 2000);
                              }}
                              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:text-white"
                            >
                              {copiedCodeToast ? (
                                <>
                                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                                  <span className="text-emerald-400 font-medium">Copied!</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="h-3.5 w-3.5" />
                                  <span>Copy Markup</span>
                                </>
                              )}
                            </button>
                          </div>
                        </div>

                        <div className="max-h-72 overflow-y-auto rounded-xl bg-slate-900/90 p-4 border border-slate-800 font-mono text-[11px] text-slate-300 whitespace-pre leading-relaxed select-all">
                          {activePageCode || "<!-- Loading or generating page markup... -->"}
                        </div>
                      </div>
                    )}

                    {/* Live Browser Mockup Container */}
                    <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
                      {/* Chrome Browser Frame Header */}
                      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-2.5 text-xs">
                        <div className="flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80 inline-block"></span>
                          <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80 inline-block"></span>
                          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
                          <span className="text-slate-400 font-mono text-[11px] ml-2 hidden sm:inline">
                            Live Tailwind Multi-Page Engine
                          </span>
                        </div>

                        {/* Address Bar */}
                        <div className="flex-1 max-w-lg mx-3">
                          <div className="flex items-center gap-2 rounded-lg bg-slate-950 border border-slate-800 px-3 py-1 font-mono text-[11px] text-slate-300">
                            <Globe className="h-3 w-3 text-emerald-400 flex-shrink-0" />
                            <span className="truncate">{currentPreviewUrl}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setIframeKey((prev) => prev + 1)}
                            title="Reload Preview"
                            className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
                          >
                            <RefreshCw className="h-3.5 w-3.5" />
                          </button>
                          <a
                            href={currentPreviewUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Test In New Tab"
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-md border border-slate-700/70 transition-colors font-semibold"
                          >
                            <ExternalLink className="h-3.5 w-3.5 text-emerald-400" />
                            <span className="hidden sm:inline">Test In New Tab</span>
                          </a>
                        </div>
                      </div>

                      {/* Device-Responsive Iframe Frame */}
                      <div className="bg-slate-950 p-2 sm:p-4 flex justify-center">
                        <div
                          className={`w-full transition-all duration-300 rounded-xl overflow-hidden shadow-inner border border-slate-800 ${
                            deviceViewport === "mobile"
                              ? "max-w-[390px] h-[580px]"
                              : deviceViewport === "tablet"
                              ? "max-w-[768px] h-[550px]"
                              : "w-full h-[520px]"
                          }`}
                        >
                          <iframe
                            key={`${lead.id}-${demoPage}-${iframeKey}`}
                            src={currentPreviewUrl}
                            title={`${lead.business_name} - ${demoPage}`}
                            className="w-full h-full border-0 bg-white"
                            sandbox="allow-scripts allow-forms allow-same-origin"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Architecture Breakdown Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-1">
                        <div className="flex items-center gap-2 font-bold text-xs text-white">
                          <span>🏠</span>
                          <span>index.html (Home)</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">
                          Hero headline, trust badges, services preview, customer reviews & CTA.
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-1">
                        <div className="flex items-center gap-2 font-bold text-xs text-white">
                          <span>ℹ️</span>
                          <span>about.html (Story)</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">
                          Company backstory, 4 core pillars, standards & commitment to {lead.location || "local area"}.
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-1">
                        <div className="flex items-center gap-2 font-bold text-xs text-white">
                          <span>🛠️</span>
                          <span>services.html (Catalog)</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">
                          4-6 service packages with pricing estimates, 4-step process & FAQs.
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-1">
                        <div className="flex items-center gap-2 font-bold text-xs text-white">
                          <span>✉️</span>
                          <span>contact.html (Booking)</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">
                          Interactive consultation form with live JavaScript confirmation modal & local map card.
                        </p>
                      </div>
                    </div>

                    {/* Quick Advance Status Banner */}
                    {lead.status !== "demo_generated" && lead.status !== "contacted" && lead.status !== "converted" && (
                      <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 flex flex-wrap items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                          <span className="text-xs text-slate-200">
                            Demo is ready to include in your outreach pitch. Advance this lead's pipeline status?
                          </span>
                        </div>
                        <button
                          onClick={() => onUpdateStatus(lead.id, "demo_generated")}
                          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs active:scale-95 transition-all shadow-md shadow-emerald-600/30"
                        >
                          Mark as Demo Ready
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Empty State Card */
                  <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-950/30 p-12 text-center space-y-4">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                      <Layout className="h-8 w-8" />
                    </div>
                    <div className="max-w-md mx-auto space-y-1.5">
                      <h4 className="text-base font-bold text-white">No Multi-Page Demo Generated Yet</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Generate a bespoke, 4-page Tailwind prototype specifically tailored to{" "}
                        <strong className="text-slate-200">{lead.business_name}</strong> in {lead.location || "your target market"}.
                      </p>
                    </div>

                    <div className="pt-2">
                      <button
                        onClick={handleTriggerGenerateDemo}
                        disabled={isGeneratingDemo}
                        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 px-6 py-3 text-xs font-bold text-white shadow-xl shadow-emerald-500/20 hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                      >
                        {isGeneratingDemo ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Generating Multi-Page Demo...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            <span>Generate 4-Page Demo Now</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-3.5 bg-slate-950/50 text-xs text-slate-500">
          <span>Created: {new Date(lead.created_at).toLocaleDateString()}</span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            data-testid="lead-drawer-footer-close-btn"
            className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 font-medium text-slate-200 hover:bg-slate-700 transition-colors cursor-pointer"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
};
