import React from "react";
import {
  Building2,
  Users,
  HardDrive,
  Scale,
  BellRing,
  KeyRound,
  ExternalLink,
} from "lucide-react";

export function Sidebar({ activeTab, onSelectTab, pendingApprovalsCount = 0 }) {
  const navItems = [
    {
      id: "tenants",
      label: "Tenant & Storage",
      subtitle: "Onboarding & Cloud Setup",
      icon: Building2,
    },
    {
      id: "iam",
      label: "Directory IAM",
      subtitle: "Umani, Agenti AI & Ruoli",
      icon: Users,
    },
    {
      id: "storage",
      label: "10 Domini Persistenti",
      subtitle: "Storage Cloud & Anti-Quota",
      icon: HardDrive,
    },
    {
      id: "delegation",
      label: "Delegation Engine",
      subtitle: "Contratti & Guardiani Anti-Chrimat",
      icon: Scale,
    },
    {
      id: "approvals",
      label: "Approval Hub (HITL)",
      subtitle: "Autorizzazioni & Notifiche",
      icon: BellRing,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : null,
    },
    {
      id: "connect",
      label: "Org3 Connect",
      subtitle: "Token API & Tool Gateway",
      icon: KeyRound,
    },
  ];

  return (
    <aside className="w-64 border-r border-dark-700 bg-dark-900 flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-[11px] font-mono uppercase tracking-wider text-neutral-500 font-semibold">
          Control Plane Modules
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition ${
                isActive
                  ? "bg-dark-800 text-white border border-dark-600 shadow-sm"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-dark-850"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-md flex items-center justify-center ${
                    isActive ? "bg-accent-orange/10 text-accent-orange" : "bg-dark-800 text-neutral-400"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-medium leading-tight">{item.label}</div>
                  <div className="text-[11px] text-neutral-500 leading-tight mt-0.5">{item.subtitle}</div>
                </div>
              </div>

              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-mono font-bold rounded-full bg-accent-orange text-white">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Connected Products Footer */}
      <div className="p-4 border-t border-dark-700/80 bg-dark-950/40 space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-wider text-neutral-500 font-semibold px-1">
          Connected Ecosystem
        </div>

        <a
          href="https://cuprite.godigix.com"
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between p-2 rounded-md bg-dark-850 hover:bg-dark-800 border border-dark-700 text-xs text-neutral-300 transition group"
        >
          <div>
            <div className="font-medium text-white flex items-center gap-1.5">
              <span>Structura OS</span>
              <span className="w-1.5 h-1.5 rounded-full bg-accent-emerald"></span>
            </div>
            <div className="text-[10px] text-neutral-500">cuprite.godigix.com</div>
          </div>
          <ExternalLink className="w-3.5 h-3.5 text-neutral-500 group-hover:text-neutral-300" />
        </a>

        <a
          href="https://memory.godigix.com"
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between p-2 rounded-md bg-dark-850 hover:bg-dark-800 border border-dark-700 text-xs text-neutral-300 transition group"
        >
          <div>
            <div className="font-medium text-white flex items-center gap-1.5">
              <span>Memograph Fabric</span>
              <span className="w-1.5 h-1.5 rounded-full bg-accent-emerald"></span>
            </div>
            <div className="text-[10px] text-neutral-500">memory.godigix.com</div>
          </div>
          <ExternalLink className="w-3.5 h-3.5 text-neutral-500 group-hover:text-neutral-300" />
        </a>
      </div>
    </aside>
  );
}
