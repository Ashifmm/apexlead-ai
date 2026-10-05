"use client";

import React from "react";
import { Users, Globe2, Mail, Layout, TrendingUp, AlertTriangle } from "lucide-react";
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
            className="glass-panel h-28 animate-pulse rounded-2xl p-4"
          >
            <div className="h-4 w-20 rounded bg-slate-800 mb-3" />
            <div className="h-8 w-12 rounded bg-slate-800" />
          </div>
        ))}
      </div>
    );
  }

  const noWebsitePercentage = stats.total_leads > 0
    ? Math.round((stats.no_website_count / stats.total_leads) * 100)
    : 0;

  const cards = [
    {
      label: "Total Leads",
      value: stats.total_leads,
      subtitle: "In active pipeline",
      icon: Users,
      iconColor: "text-blue-400",
      bgColor: "from-blue-500/10 to-indigo-500/5",
      borderColor: "border-blue-500/20",
    },
    {
      label: "Needs Website",
      value: stats.no_website_count,
      subtitle: `${noWebsitePercentage}% prime opportunities`,
      icon: AlertTriangle,
      iconColor: "text-amber-400",
      bgColor: "from-amber-500/10 to-orange-500/5",
      borderColor: "border-amber-500/20",
      highlight: true,
    },
    {
      label: "Outreach Ready",
      value: stats.outreach_ready_count,
      subtitle: "AI emails & DMs prepared",
      icon: Mail,
      iconColor: "text-purple-400",
      bgColor: "from-purple-500/10 to-pink-500/5",
      borderColor: "border-purple-500/20",
    },
    {
      label: "Demos Ready",
      value: stats.demos_ready_count,
      subtitle: "Personalized prototypes",
      icon: Layout,
      iconColor: "text-emerald-400",
      bgColor: "from-emerald-500/10 to-teal-500/5",
      borderColor: "border-emerald-500/20",
    },
    {
      label: "Avg. Lead Score",
      value: `${stats.average_score}/100`,
      subtitle: "Opportunity index",
      icon: TrendingUp,
      iconColor: "text-indigo-400",
      bgColor: "from-indigo-500/10 to-violet-500/5",
      borderColor: "border-indigo-500/20",
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
              <span className="text-xs font-medium text-slate-400">{card.label}</span>
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
