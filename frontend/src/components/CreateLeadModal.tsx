"use client";

import React, { useState } from "react";
import { X, Building2, Plus, AlertCircle } from "lucide-react";
import { LeadCreateInput } from "@/types/lead";

interface CreateLeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (leadData: LeadCreateInput) => Promise<void>;
}

export const CreateLeadModal: React.FC<CreateLeadModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [formData, setFormData] = useState<LeadCreateInput>({
    business_name: "",
    industry: "",
    location: "",
    website_url: "",
    email: "",
    phone: "",
    instagram_handle: "",
    notes: "",
    source: "manual",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.business_name.trim()) {
      setError("Business name is required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit(formData);
      // Reset form
      setFormData({
        business_name: "",
        industry: "",
        location: "",
        website_url: "",
        email: "",
        phone: "",
        instagram_handle: "",
        notes: "",
        source: "manual",
      });
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create lead.");
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
              <h2 className="text-base font-bold text-white">Add Target Business</h2>
              <p className="text-xs text-slate-400">Add a prospect to your web agency pipeline</p>
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

          {/* Business Name (Required) */}
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">
              Business Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.business_name}
              onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
              placeholder="e.g. Apex Dental Spa"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Industry */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Industry / Niche
              </label>
              <input
                type="text"
                value={formData.industry || ""}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                placeholder="e.g. Dental, Roofing, Restaurant"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>

            {/* Location */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                City, State
              </label>
              <input
                type="text"
                value={formData.location || ""}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g. Austin, TX"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Website URL */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Existing Website URL (leave blank if they have none)
            </label>
            <input
              type="text"
              value={formData.website_url || ""}
              onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
              placeholder="e.g. https://example.com (or leave empty if no website)"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            {/* Email */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email || ""}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="contact@biz.com"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>

            {/* Phone */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone || ""}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="(555) 000-0000"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>

            {/* Instagram */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Instagram
              </label>
              <input
                type="text"
                value={formData.instagram_handle || ""}
                onChange={(e) => setFormData({ ...formData, instagram_handle: e.target.value })}
                placeholder="@business"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Internal Notes
            </label>
            <textarea
              rows={2}
              value={formData.notes || ""}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="e.g. Found on Google Maps, lots of positive reviews but terrible/missing site."
              className="w-full rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
            />
          </div>

          {/* Action buttons */}
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
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-500/20 hover:opacity-95 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              <span>{isSubmitting ? "Adding..." : "Add to Pipeline"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
