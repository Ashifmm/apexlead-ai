export interface Lead {
  id: number;
  business_name: string;
  industry?: string | null;
  location?: string | null;
  website_url?: string | null;
  has_website: boolean;
  email?: string | null;
  phone?: string | null;
  instagram_handle?: string | null;
  source_post_url?: string | null;
  comment_text?: string | null;
  source: string;
  status: 'Intent Detected' | 'DM Drafted' | 'DM Queued' | 'Sent' | 'Pitch Sent' | 'contacted' | 'converted' | string;
  lead_score: number;
  score_reasons?: string | null;
  website_analysis?: string | null;
  outreach_email_subject?: string | null;
  outreach_email_body?: string | null;
  outreach_instagram_dm?: string | null;
  demo_url?: string | null;
  demo_preview_html?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadCreateInput {
  business_name: string;
  industry?: string;
  location?: string;
  website_url?: string;
  has_website?: boolean;
  email?: string;
  phone?: string;
  instagram_handle?: string;
  source_post_url?: string;
  comment_text?: string;
  source?: string;
  status?: string;
  lead_score?: number;
  notes?: string;
}

export interface LeadUpdateInput {
  business_name?: string;
  industry?: string;
  location?: string;
  website_url?: string;
  has_website?: boolean;
  email?: string;
  phone?: string;
  instagram_handle?: string;
  source_post_url?: string;
  comment_text?: string;
  source?: string;
  status?: string;
  lead_score?: number;
  score_reasons?: string;
  website_analysis?: string;
  outreach_email_subject?: string;
  outreach_email_body?: string;
  outreach_instagram_dm?: string;
  demo_url?: string;
  demo_preview_html?: string;
  notes?: string;
}

export interface LeadStats {
  total_leads: number;
  intent_detected_count?: number;
  dm_drafted_count?: number;
  dm_queued_count?: number;
  sent_count?: number;
  average_score: number;
  status_breakdown: Record<string, number>;
  // Legacy compatibility fields
  no_website_count?: number;
  has_website_count?: number;
  demos_ready_count?: number;
  outreach_ready_count?: number;
  contacted_count?: number;
  converted_count?: number;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FilterParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  has_website?: boolean;
  min_score?: number;
}

export interface ColdEmail {
  subject: string;
  body: string;
}

export interface LeadAnalysisResult {
  lead_score: number;
  priority: 'low' | 'medium' | 'high';
  website_needed: boolean;
  pain_points: string[];
  recommended_solution: string;
  personalized_instagram_dm: string;
  cold_email: ColdEmail;
}

export interface LeadAnalysisResponse {
  success: boolean;
  lead_id?: number | null;
  analysis?: LeadAnalysisResult | null;
  error?: string | null;
}

export interface WebsiteAuditScores {
  overall_score: number;
  design_score: number;
  mobile_score: number;
  conversion_score: number;
}

export interface WebsiteAuditResult {
  target_url: string;
  scores: WebsiteAuditScores;
  redesign_opportunity: 'low' | 'medium' | 'high';
  issues: string[];
  improvements: string[];
  technical_signals: Record<string, any>;
  summary: string;
}

export interface WebsiteAnalyzeResponse {
  success: boolean;
  status: 'success' | 'unreachable' | 'no_website' | 'error' | string;
  lead_id?: number | null;
  audit?: WebsiteAuditResult | null;
  error?: string | null;
}

export interface DemoGenerateRequest {
  lead_id?: number;
  custom_instructions?: string;
  theme_color?: string;
}

export interface DemoGenerateResponse {
  success: boolean;
  lead_id: number;
  demo_url: string;
  business_name: string;
  industry?: string | null;
  message: string;
  preview_snippet?: string | null;
  error?: string | null;
  pages_generated?: string[];
}

export interface DemoDetailResponse {
  lead_id: number;
  business_name: string;
  demo_url?: string | null;
  has_demo: boolean;
  pages: Record<string, string>;
}
