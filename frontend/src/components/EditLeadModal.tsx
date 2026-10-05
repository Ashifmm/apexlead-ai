"use client";

import React, { useState, useEffect } from "react";
import { X, Building2, Check, AlertCircle } from "lucide-react";
import { Lead, LeadUpdateInput } from "@/types/lead";

interface EditLeadModalProps {
  lead: Lead | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: number, data: LeadUpdateInput) => Promise<void>;
}

export const EditLeadModal: React.FC<EditLeadModalProps> = ({
  lead,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<LeadUpdateInput>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (lead) {
      setFormData({
        business_name: lead.business_name,
        industry: lead.industry || "",
        location: lead.location || "",
        website_url: lead.website_url || "",
        email: lead.email || "",
        phone: lead.phone || "",
        instagram_handle: lead.instagram_handle || "",
        status: lead.status,
        lead_score: lead.lead_score,
        notes: lead.notes || "",
      });
    }
  }, [lead]);

  if (!isOpen || !lead) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.business_name?.trim()) {
      setError("Business name cannot be empty.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit(lead.id, formData);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to update lead.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Edit Lead #{lead.id}</h2>
              <p className="text-xs text-slate-400">Update business information and status</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">
              Business Name
            </label>
            <input
              type="text"
              required
              value={formData.business_name || ""}
              onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Industry
              </label>
              <input
                type="text"
                value={formData.industry || ""}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Location
              </label>
              <input
                type="text"
                value={formData.location || ""}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Pipeline Status
              </label>
              <select
                value={formData.status || "new"}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 outline-none focus:border-indigo-500"
              >
                <option value="new">New</option>
                <option value="analyzed">Analyzed</option>
                <option value="scored">Scored</option>
                <option value="outreach_generated">Outreach Ready</option>
                <option value="demo_generated">Demo Generated</option>
                <option value="contacted">Contacted</option>
                <option value="converted">Converted</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Lead Score (0 - 100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.lead_score ?? 0}
                onChange={(e) => setFormData({ ...formData, lead_score: parseInt(e.target.value) || 0 })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Website URL
            </label>
            <input
              type="text"
              value={formData.website_url || ""}
              onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Instagram Handle</label>
              <input
                type="text"
                value={formData.instagram_handle || ""}
                onChange={(e) => setFormData({ ...formData, instagram_handle: e.target.value })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 outline-none focus:border-pink-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Phone</label>
              <input
                type="tel"
                value={formData.phone || ""}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Internal Notes</label>
            <textarea
              rows={2}
              value={formData.notes || ""}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-100 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              <span>{isSubmitting ? "Saving..." : "Save Changes"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
