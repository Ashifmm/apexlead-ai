"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Header } from "@/components/Header";
import { StatsOverview } from "@/components/StatsOverview";
import { FilterBar } from "@/components/FilterBar";
import { LeadTable, getLeadPriority } from "@/components/LeadTable";
import { LeadDetailModal } from "@/components/LeadDetailModal";
import { CreateLeadModal } from "@/components/CreateLeadModal";
import { EditLeadModal } from "@/components/EditLeadModal";
import { ScanInstagramModal } from "@/components/ScanInstagramModal";
import { AutonomousStreamModal } from "@/components/AutonomousStreamModal";
import {
  fetchLeads,
  fetchLeadStats,
  createLead,
  updateLead,
  updateLeadStatus,
  deleteLead,
  seedSampleLeads,
  scanInstagramIntent,
  queueLead,
  markLeadSent,
  regenerateLeadDM,
  dispatchInstagramBatch,
  fetchInstagramOutreachStatus,
  fetchAgentStatus,
  toggleAgent,
  triggerAgentHarvest,
  AgentStatus,
  BACKEND_HOST,
  checkBackendHealth,
} from "@/lib/api";
import { Lead, LeadCreateInput, LeadStats, LeadUpdateInput } from "@/types/lead";
import { CheckCircle2, AlertTriangle, X } from "lucide-react";

export default function DashboardPage() {
  // State
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);

  // Filters
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [industryFilter, setIndustryFilter] = useState<string>("all");

  // Modals & Active Drawer
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const selectedLeadIdRef = React.useRef<number | null>(null);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [isScanInstagramOpen, setIsScanInstagramOpen] = useState<boolean>(false);
  const [isScanningInstagram, setIsScanningInstagram] = useState<boolean>(false);

  // Outreach Automation State
  const [dailyIgLimit, setDailyIgLimit] = useState<number>(15);
  const [isDispatchingIg, setIsDispatchingIg] = useState<boolean>(false);
  const [isRegeneratingDM, setIsRegeneratingDM] = useState<boolean>(false);
  const [igOutreachStatus, setIgOutreachStatus] = useState<{
    daily_limit: number;
    dispatched_today: number;
    pending_queue: number;
    available_quota: number;
  } | null>(null);

  // Autonomous Background Agent Telemetry State
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [isAgentStreamOpen, setIsAgentStreamOpen] = useState<boolean>(false);
  const [isHarvestingAgent, setIsHarvestingAgent] = useState<boolean>(false);

  // Sync ref with selectedLead state
  useEffect(() => {
    selectedLeadIdRef.current = selectedLead ? selectedLead.id : null;
  }, [selectedLead]);

  const handleCloseLeadModal = useCallback(() => {
    selectedLeadIdRef.current = null;
    setSelectedLead(null);
  }, []);

  // Toast Notification
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  // Load Data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Check health
      try {
        const health = await checkBackendHealth();
        setIsBackendConnected(health.status === "healthy" || health.status === "degraded");
      } catch {
        setIsBackendConnected(false);
      }

      // 2. Fetch leads with active filters
      const leadsRes = await fetchLeads({
        search: search.trim() || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        page_size: 100,
      });
      setLeads(leadsRes.items);

      // Keep selectedLead in sync if actively open
      if (selectedLeadIdRef.current !== null) {
        const fresh = leadsRes.items.find((l) => l.id === selectedLeadIdRef.current);
        if (fresh) setSelectedLead(fresh);
      }

      // 3. Fetch aggregated stats
      const statsRes = await fetchLeadStats();
      setStats(statsRes);

      // 4. Fetch Instagram outreach status
      try {
        const outStatus = await fetchInstagramOutreachStatus(dailyIgLimit);
        setIgOutreachStatus(outStatus);
      } catch {
        // Soft fail
      }

      // 5. Fetch Autonomous Background Agent Telemetry
      try {
        const aStatus = await fetchAgentStatus();
        setAgentStatus(aStatus);
      } catch {
        // Soft fail
      }
    } catch (err: any) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, dailyIgLimit]);

  // Initial load and filter change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Health poll check every 15s
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        await checkBackendHealth();
        setIsBackendConnected(true);
      } catch {
        setIsBackendConnected(false);
      }
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Autonomous Agent Telemetry poll every 8s
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const aStatus = await fetchAgentStatus();
        setAgentStatus(aStatus);
      } catch {}
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  // Compute available industries from current leads
  const availableIndustries = useMemo(() => {
    const set = new Set<string>();
    leads.forEach((l) => {
      if (l.industry && l.industry.trim()) set.add(l.industry.trim());
    });
    return Array.from(set).sort();
  }, [leads]);

  // Client-side filtering for priority and industry
  const displayedLeads = useMemo(() => {
    return leads.filter((lead) => {
      if (priorityFilter !== "all") {
        const p = getLeadPriority(lead);
        if (p !== priorityFilter) return false;
      }
      if (industryFilter !== "all") {
        if ((lead.industry || "").toLowerCase() !== industryFilter.toLowerCase()) {
          return false;
        }
      }
      return true;
    });
  }, [leads, priorityFilter, industryFilter]);

  // Handlers
  const handleSeedData = async () => {
    try {
      setIsSeeding(true);
      const res = await seedSampleLeads();
      showToast(res.message, "success");
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to seed demo data", "error");
    } finally {
      setIsSeeding(false);
    }
  };

  const handleScanInstagram = async (params: {
    hashtag?: string;
    keyword?: string;
    target_account?: string;
    count: number;
  }) => {
    setIsScanningInstagram(true);
    try {
      const targetLabel = params.target_account
        ? `@${params.target_account}`
        : `#${params.hashtag || "webdesign"}`;
      showToast(`Scanning Instagram comments & intent across ${targetLabel}...`, "success");
      const res = await scanInstagramIntent(params);
      showToast(res.message || `Discovered ${res.count} Instagram intent leads!`, "success");
      setIsScanInstagramOpen(false);
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to scan Instagram intent", "error");
    } finally {
      setIsScanningInstagram(false);
    }
  };

  const handleQueueLead = async (id: number) => {
    try {
      const updated = await queueLead(id);
      showToast(`Lead @${updated.instagram_handle || updated.business_name} queued for outreach!`, "success");
      if (selectedLead?.id === id) {
        setSelectedLead(updated);
      }
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to queue lead", "error");
    }
  };

  const handleMarkSent = async (id: number) => {
    try {
      const updated = await markLeadSent(id);
      showToast(`Lead marked as Sent! 🚀`, "success");
      if (selectedLead?.id === id) {
        setSelectedLead(updated);
      }
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to mark as sent", "error");
    }
  };

  const handleRegenerateDM = async (id: number) => {
    try {
      setIsRegeneratingDM(true);
      showToast("Personalizing DM with Gemini AI...", "success");
      const updated = await regenerateLeadDM(id);
      showToast("Personalized DM updated!", "success");
      if (selectedLead?.id === id) {
        setSelectedLead(updated);
      }
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to regenerate DM", "error");
    } finally {
      setIsRegeneratingDM(false);
    }
  };

  const handleDispatchIgBatch = async () => {
    setIsDispatchingIg(true);
    try {
      showToast(`Dispatching automated Instagram DM batch (Limit: ${dailyIgLimit}/day)...`, "success");
      const res = await dispatchInstagramBatch({ daily_limit: dailyIgLimit });
      showToast(res.message, res.dispatched_count > 0 ? "success" : "error");
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to dispatch Instagram DM batch", "error");
    } finally {
      setIsDispatchingIg(false);
    }
  };

  const handleToggleAgent = async () => {
    try {
      const res = await toggleAgent();
      setAgentStatus(res.status);
      showToast(res.message, "success");
    } catch (err: any) {
      showToast(err.message || "Failed to toggle autonomous agent", "error");
    }
  };

  const handleTriggerAgentHarvest = async () => {
    setIsHarvestingAgent(true);
    try {
      showToast("Triggering live autonomous intent harvest...", "success");
      const res = await triggerAgentHarvest();
      setAgentStatus(res.status);
      showToast(res.message, "success");
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to harvest live intent", "error");
    } finally {
      setIsHarvestingAgent(false);
    }
  };

  const handleCreateLead = async (leadData: LeadCreateInput) => {
    await createLead(leadData);
    showToast(`Lead "${leadData.business_name}" added to pipeline!`, "success");
    await loadData();
  };

  const handleUpdateLead = async (id: number, updateData: LeadUpdateInput) => {
    const updated = await updateLead(id, updateData);
    showToast(`Lead updated successfully!`, "success");
    if (selectedLead && selectedLead.id === id) {
      setSelectedLead(updated);
    }
    await loadData();
  };

  const handleQuickStatusUpdate = async (id: number, newStatus: string) => {
    try {
      let updated: Lead;
      try {
        updated = await updateLeadStatus(id, newStatus);
      } catch {
        updated = await updateLead(id, { status: newStatus });
      }
      setSelectedLead(updated);
      showToast(`Status updated to "${newStatus}"`, "success");
      await loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to update status", "error");
    }
  };

  const handleDeleteLead = async (lead: Lead) => {
    if (confirm(`Are you sure you want to delete "${lead.business_name}"?`)) {
      try {
        await deleteLead(lead.id);
        showToast(`Lead "${lead.business_name}" deleted.`, "success");
        if (selectedLead?.id === lead.id) {
          selectedLeadIdRef.current = null;
          setSelectedLead(null);
        }
        await loadData();
      } catch (err: any) {
        showToast(err.message || "Failed to delete lead", "error");
      }
    }
  };

  const handleSaveOutreachDrafts = async (
    id: number,
    data: {
      outreach_instagram_dm?: string;
      status?: string;
      notes?: string;
    }
  ) => {
    const updated = await updateLead(id, data);
    setSelectedLead(updated);
    showToast(`Outreach drafts saved!`, "success");
    await loadData();
  };

  return (
    <div className="min-h-screen bg-[#0B0F19]">
      {/* Toast Alert */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 rounded-xl border border-slate-700 bg-slate-900/95 px-4 py-3 text-sm shadow-2xl backdrop-blur-md animate-in slide-in-from-bottom-2">
          {toast.type === "success" ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-rose-400 flex-shrink-0" />
          )}
          <span className="text-slate-200">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="ml-2 rounded-lg p-1 text-slate-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Main Header */}
      <Header
        isBackendConnected={isBackendConnected}
        isSeeding={isSeeding}
        onSeedData={handleSeedData}
        onRefresh={loadData}
        onOpenScanPosts={() => setIsScanInstagramOpen(true)}
        dailyIgLimit={dailyIgLimit}
        onDailyIgLimitChange={setDailyIgLimit}
        onDispatchIgBatch={handleDispatchIgBatch}
        isDispatchingIg={isDispatchingIg}
        agentStatus={agentStatus}
        onToggleAgent={handleToggleAgent}
        onOpenAgentStream={() => setIsAgentStreamOpen(true)}
      />

      {/* Backend Disconnection Banner */}
      {!isBackendConnected && !loading && (
        <div className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-center text-xs text-amber-300">
          ⚠️ Backend is not running or unreachable at <code className="font-mono font-semibold">{BACKEND_HOST}</code>. Ensure FastAPI server is active.
        </div>
      )}

      {/* Content Container */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        {/* Metric Cards */}
        <StatsOverview stats={stats} loading={loading} />

        {/* Filter & Actions Bar */}
        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <FilterBar
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusChange={setStatusFilter}
            priorityFilter={priorityFilter}
            onPriorityChange={setPriorityFilter}
            industryFilter={industryFilter}
            onIndustryChange={setIndustryFilter}
            availableIndustries={availableIndustries}
            onOpenCreateModal={() => setIsCreateOpen(true)}
            onOpenScanPostsModal={() => setIsScanInstagramOpen(true)}
            onDispatchBatch={handleDispatchIgBatch}
            isDispatching={isDispatchingIg}
          />
        </div>

        {/* Leads Table */}
        <LeadTable
          leads={displayedLeads}
          loading={loading}
          onSelectLead={(lead) => {
            selectedLeadIdRef.current = lead.id;
            setSelectedLead(lead);
          }}
          onDeleteLead={handleDeleteLead}
          onQueueLead={handleQueueLead}
          onMarkSent={handleMarkSent}
          onRegenerateDM={handleRegenerateDM}
          onNotify={showToast}
          onOpenScanPosts={() => setIsScanInstagramOpen(true)}
        />
      </main>

      {/* Modals & Drawers */}
      <LeadDetailModal
        lead={selectedLead}
        isOpen={Boolean(selectedLead)}
        onClose={handleCloseLeadModal}
        onUpdateStatus={handleQuickStatusUpdate}
        onSaveOutreachDrafts={handleSaveOutreachDrafts}
        onRegenerateDM={handleRegenerateDM}
        onQueueLead={handleQueueLead}
        onMarkSent={handleMarkSent}
        isRegeneratingDM={isRegeneratingDM}
      />

      <CreateLeadModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateLead}
      />

      <EditLeadModal
        lead={editingLead}
        isOpen={Boolean(editingLead)}
        onClose={() => setEditingLead(null)}
        onSubmit={handleUpdateLead}
      />

      <ScanInstagramModal
        isOpen={isScanInstagramOpen}
        onClose={() => setIsScanInstagramOpen(false)}
        onScan={handleScanInstagram}
        isLoading={isScanningInstagram}
      />

      <AutonomousStreamModal
        isOpen={isAgentStreamOpen}
        onClose={() => setIsAgentStreamOpen(false)}
        status={agentStatus}
        onToggleAgent={handleToggleAgent}
        onTriggerHarvest={handleTriggerAgentHarvest}
        isHarvesting={isHarvestingAgent}
      />
    </div>
  );
}
