import React from "react";
import { Clock, GitFork, Users, AlertTriangle } from "lucide-react";

export default function MetricsCards({ simulation }) {
  if (!simulation) return null;

  const cards = [
    {
      title: "Injected Delay",
      value: `+${simulation.injected_delay_min} min`,
      sub: simulation.root_trip_name,
      icon: Clock,
      color: "text-red-400 bg-red-500/10 border-red-500/20",
    },
    {
      title: "Knock-on Trains",
      value: simulation.total_affected_trips,
      sub: "Secondary trip delays",
      icon: GitFork,
      color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    },
    {
      title: "Broken Transfers",
      value: simulation.total_broken_transfers,
      sub: "Missed connection routes",
      icon: AlertTriangle,
      color: "text-orange-400 bg-orange-500/10 border-orange-500/20",
    },
    {
      title: "Stranded Passengers",
      value: simulation.total_affected_passengers,
      sub: "Volume impacted",
      icon: Users,
      color: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div key={i} className={`p-4 rounded-xl border ${c.color} flex items-center justify-between`}>
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">{c.title}</p>
              <h3 className="text-2xl font-bold mt-1 text-slate-100">{c.value}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{c.sub}</p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900/50">
              <Icon className="w-6 h-6" />
            </div>
          </div>
        );
      })}
    </div>
  );
}