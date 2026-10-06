import React from "react";
import { ShieldAlert, Zap, Globe, Layers, UserCheck } from "lucide-react";

export function Navbar({ currentOrg, organizations, onSelectOrg, onNewOrg }) {
  return (
    <header className="h-16 border-b border-dark-700 bg-dark-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Workspace */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-orange to-amber-600 flex items-center justify-center shadow-lg shadow-accent-orange/20">
            <span className="font-mono font-bold text-white text-base">O3</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-tight text-lg">Org3 Platform</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-dark-700 text-neutral-300 border border-dark-600">
                v3.3.0
              </span>
            </div>
            <p className="text-xs text-neutral-400 font-mono">Sovereign Governance & Control Plane</p>
          </div>
        </div>

        <div className="h-6 w-px bg-dark-700 mx-2" />

        {/* Tenant Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-neutral-400">Azienda:</span>
          <select
            value={currentOrg?.id || ""}
            onChange={(e) => {
              if (e.target.value === "new") {
                onNewOrg();
              } else {
                const found = organizations.find((o) => o.id === e.target.value);
                if (found) onSelectOrg(found);
              }
            }}
            className="bg-dark-800 text-sm font-medium text-neutral-100 border border-dark-700 rounded-md px-3 py-1.5 focus:outline-none focus:border-accent-orange transition"
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name} ({org.slug})
              </option>
            ))}
            <option value="new">+ Crea Nuova Azienda...</option>
          </select>

          {currentOrg && (
            <span
              className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded-full font-semibold border ${
                currentOrg.plan === "enterprise"
                  ? "bg-accent-violet/10 text-accent-violet border-accent-violet/30"
                  : currentOrg.plan === "business"
                  ? "bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30"
                  : "bg-neutral-800 text-neutral-400 border-neutral-700"
              }`}
            >
              Piano {currentOrg.plan}
            </span>
          )}
        </div>
      </div>

      {/* God Mode & Health Indicators */}
      <div className="flex items-center gap-4">
        {/* God Mode Badge for Nunzio */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-accent-orange/10 border border-accent-orange/30 text-accent-orange">
          <ShieldAlert className="w-4 h-4 animate-pulse" />
          <div className="text-left">
            <div className="text-xs font-bold leading-tight font-mono">GOD MODE: ACTIVE</div>
            <div className="text-[10px] opacity-80 leading-tight">Nunzio Lella (Master Assoluto)</div>
          </div>
        </div>

        {/* System Health */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-dark-800 border border-dark-700 text-xs text-neutral-300">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-ping" />
          <span className="font-mono text-[11px]">API: Online</span>
        </div>
      </div>
    </header>
  );
}
