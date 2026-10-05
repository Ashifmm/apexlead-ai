import { FilterParams, Lead, LeadCreateInput, LeadListResponse, LeadStats, LeadUpdateInput } from "@/types/lead";

const RAW_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "https://apexlead-ai.onrender.com"
).replace(/\/+$/, "");


// Ensure API_BASE_URL has /api/v1 prefix for endpoints
export const API_BASE_URL = RAW_BASE_URL.endsWith("/api/v1")
  ? RAW_BASE_URL
  : `${RAW_BASE_URL}/api/v1`;

// Root host URL for static demos, docs, or health
export const BACKEND_HOST = RAW_BASE_URL.replace(/\/api\/v1\/?$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorMessage = `API error: ${res.statusText}`;
      try {
        const errJson = await res.json();
        errorMessage = errJson.detail || errorMessage;
      } catch {
        // Fallback to text status
      }
      throw new ApiError(errorMessage, res.status);
    }
    return (await res.json()) as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network / connection refused error
    throw new ApiError(
      "Unable to connect to FastAPI backend. Ensure backend is running at " + API_BASE_URL,
      0
    );
  }
}

export async function checkBackendHealth(): Promise<{ status: string; gemini_api_configured: boolean; database_connected: boolean }> {
  return request("/health");
}

export async function fetchLeads(params: FilterParams = {}): Promise<LeadListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());
  if (params.search) query.set("search", params.search);
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.has_website !== undefined) query.set("has_website", params.has_website.toString());
  if (params.min_score !== undefined) query.set("min_score", params.min_score.toString());

  const queryString = query.toString();
  const endpoint = `/leads${queryString ? `?${queryString}` : ""}`;
  return request<LeadListResponse>(endpoint);
}

export async function fetchLeadStats(): Promise<LeadStats> {
  return request<LeadStats>("/leads/stats");
}

export async function fetchLeadById(id: number): Promise<Lead> {
  return request<Lead>(`/leads/${id}`);
}

export async function createLead(data: LeadCreateInput): Promise<Lead> {
  return request<Lead>("/leads", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateLead(id: number, data: LeadUpdateInput): Promise<Lead> {
  return request<Lead>(`/leads/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteLead(id: number): Promise<Lead> {
  return request<Lead>(`/leads/${id}`, {
    method: "DELETE",
  });
}

export async function seedSampleLeads(): Promise<{ message: string; inserted: number }> {
  return request<{ message: string; inserted: number }>("/leads/seed", {
    method: "POST",
  });
}

export async function scanInstagramIntent(data: {
  niche?: string;
  count?: number;
  hashtag?: string;
  keyword?: string;
  target_account?: string;
}): Promise<{ message: string; niche?: string; count: number; leads: Lead[] }> {
  return request("/leads/scan-instagram", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function queueLead(leadId: number): Promise<Lead> {
  return request<Lead>(`/leads/${leadId}/queue`, {
    method: "POST",
  });
}

export async function markLeadSent(leadId: number): Promise<Lead> {
  return request<Lead>(`/leads/${leadId}/mark-sent`, {
    method: "POST",
  });
}

export async function regenerateLeadDM(leadId: number): Promise<Lead> {
  return request<Lead>(`/leads/${leadId}/regenerate-dm`, {
    method: "POST",
  });
}

export async function dispatchInstagramBatch(data: {
  daily_limit?: number;
}): Promise<{
  message: string;
  dispatched_count: number;
  daily_limit: number;
  remaining_quota: number;
  dispatched_leads: Lead[];
}> {
  return request("/outreach/instagram/dispatch", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchInstagramOutreachStatus(dailyLimit: number = 15): Promise<{
  daily_limit: number;
  dispatched_today: number;
  pending_queue: number;
  available_quota: number;
}> {
  return request(`/outreach/instagram/status?daily_limit=${dailyLimit}`);
}

export async function updateLeadStatus(leadId: number, pipelineStatus: string): Promise<Lead> {
  return request<Lead>(`/leads/${leadId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ pipeline_status: pipelineStatus }),
  });
}

export async function updateLeadPipelineStatus(leadId: number, pipelineStatus: string): Promise<Lead> {
  return updateLeadStatus(leadId, pipelineStatus);
}

export interface AgentEvent {
  id: string;
  timestamp: string;
  event_type: "harvest" | "dm_sent" | "quota" | "system";
  message: string;
  meta?: Record<string, any>;
}

export interface AgentStatus {
  is_active: boolean;
  status_label: "ACTIVE" | "PAUSED" | "LIMIT REACHED";
  daily_limit: number;
  dispatched_today: number;
  available_quota: number;
  pending_queue: number;
  last_dispatched_at: string | null;
  next_run_time: string | null;
  recent_events: AgentEvent[];
}

export async function fetchAgentStatus(): Promise<AgentStatus> {
  return request<AgentStatus>("/outreach/agent/status");
}

export async function toggleAgent(): Promise<{ message: string; is_active: boolean; status: AgentStatus }> {
  return request("/outreach/agent/toggle", { method: "POST" });
}

export async function triggerAgentHarvest(): Promise<{ message: string; harvested_count: number; status: AgentStatus }> {
  return request("/outreach/agent/harvest-now", { method: "POST" });
}

