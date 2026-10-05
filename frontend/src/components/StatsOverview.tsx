"use client";

import React from "react";
import { Users, Sparkles, Send, Clock, TrendingUp } from "lucide-react";
import { LeadStats } from "@/types/lead";

interface StatsOverviewProps {
  stats: LeadStats | null;
  loading: boolean;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats, loading }) => {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="glass-panel h-28 animate-pulse rounded-2xl p-4 bg-slate-900/60"
          >
            <div className="h-4 w-20 rounded bg-slate-800 mb-3" />
            <div className="h-8 w-12 rounded bg-slate-800" />
          </div>
        ))}
      </div>
    );
  }

  const intentCount = stats.intent_detected_count ?? (stats.total_leads - (stats.sent_count || 0));
  const draftedCount = stats.dm_drafted_count ?? (stats.outreach_ready_count || 0);
  const queuedCount = stats.dm_queued_count ?? 0;
  const sentCount = stats.sent_count ?? (stats.contacted_count || 0);

  const cards = [
    {
      label: "Total Intent Leads",
      value: stats.total_leads,
      subtitle: "Active commercial prospects",
      icon: Users,
      iconColor: "text-pink-400",
      bgColor: "from-pink-500/10 to-rose-500/5",
      borderColor: "border-pink-500/20",
    },
    {
      label: "AI DMs Drafted",
      value: draftedCount,
      subtitle: "Personalized & ready to review",
      icon: Sparkles,
      iconColor: "text-amber-400",
      bgColor: "from-amber-500/10 to-orange-500/5",
      borderColor: "border-amber-500/20",
    },
    {
      label: "Dispatch Queue",
      value: queuedCount,
      subtitle: "Awaiting safe pacing interval",
      icon: Clock,
      iconColor: "text-purple-400",
      bgColor: "from-purple-500/10 to-indigo-500/5",
      borderColor: "border-purple-500/20",
      highlight: true,
    },
    {
      label: "DMs Dispatched",
      value: sentCount,
      subtitle: "Sent via 1-Click & Auto-DM",
      icon: Send,
      iconColor: "text-emerald-400",
      bgColor: "from-emerald-500/10 to-teal-500/5",
      borderColor: "border-emerald-500/20",
    },
    {
      label: "Avg. Intent Score",
      value: `${stats.average_score}%`,
      subtitle: "Commercial inquiry confidence",
      icon: TrendingUp,
      iconColor: "text-cyan-400",
      bgColor: "from-cyan-500/10 to-blue-500/5",
      borderColor: "border-cyan-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((card, idx) => {
        const IconComponent = card.icon;
        return (
          <div
            key={idx}
            className={`glass-panel glass-panel-hover relative overflow-hidden rounded-2xl border ${card.borderColor} bg-gradient-to-br ${card.bgColor} p-4.5 transition-all`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">{card.label}</span>
              <div className="rounded-lg bg-slate-900/60 p-1.5 ring-1 ring-white/10">
                <IconComponent className={`h-4 w-4 ${card.iconColor}`} />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight text-white">
                {card.value}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};
