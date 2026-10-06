import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { Sidebar } from "./components/Sidebar";
import { TenantSetup } from "./components/TenantSetup";
import { DirectoryIAM } from "./components/DirectoryIAM";
import { StorageExplorer } from "./components/StorageExplorer";
import { DelegationBuilder } from "./components/DelegationBuilder";
import { ApprovalHub } from "./components/ApprovalHub";
import { Org3Connect } from "./components/Org3Connect";
import { api } from "./api/client";
import { RefreshCw, Building2 } from "lucide-react";

export function App() {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [activeTab, setActiveTab] = useState("tenants");
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // New Organization modal state
  const [showNewOrgModal, setShowNewOrgModal] = useState(false);
  const [newSlug, setNewSlug] = useState("");
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("01nunzio.lella@gmail.com");
  const [newPlan, setNewPlan] = useState("business");

  const loadOrganizations = async () => {
    try {
      const data = await api.organizations.list();
      setOrganizations(data || []);

      if (data && data.length > 0) {
        // Preferisci symbiotic o qubitdata o il primo
        const defaultOrg =
          data.find((o) => o.slug === "symbiotic") ||
          data.find((o) => o.slug === "qubitdata") ||
          data[0];
        setCurrentOrg(defaultOrg);
      }
    } catch (err) {
      console.error("Failed to load organizations:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadPendingCount = async () => {
    if (!currentOrg?.id) return;
    try {
      const pending = await api.approvals.list(currentOrg.id, "PENDING");
      setPendingApprovalsCount(pending?.length || 0);
    } catch (err) {
      console.error("Failed to load pending count:", err);
    }
  };

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    loadPendingCount();
    const interval = setInterval(loadPendingCount, 15000);
    return () => clearInterval(interval);
  }, [currentOrg?.id]);

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    try {
      const created = await api.organizations.create({
        slug: newSlug.trim().toLowerCase(),
        name: newName.trim(),
        owner_email: newEmail.trim(),
        plan: newPlan,
      });

      setShowNewOrgModal(false);
      setNewSlug("");
      setNewName("");
      await loadOrganizations();
      setCurrentOrg(created);
    } catch (err) {
      alert("Errore creazione organizzazione: " + err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 text-white flex flex-col items-center justify-center space-y-3 font-mono text-sm">
        <RefreshCw className="w-6 h-6 animate-spin text-accent-orange" />
        <div>Inizializzazione Org3 Control Plane...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 text-neutral-100 flex flex-col">
      {/* Header */}
      <Navbar
        currentOrg={currentOrg}
        organizations={organizations}
        onSelectOrg={(org) => setCurrentOrg(org)}
        onNewOrg={() => setShowNewOrgModal(true)}
      />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
          pendingApprovalsCount={pendingApprovalsCount}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto">
          {!currentOrg ? (
            <div className="p-12 text-center max-w-md mx-auto mt-20 space-y-4 bg-dark-900 rounded-xl border border-dark-700">
              <Building2 className="w-12 h-12 text-accent-orange mx-auto" />
              <h2 className="text-xl font-bold text-white">Nessuna Organizzazione Rilevata</h2>
              <p className="text-xs text-neutral-400">
                Inizia creando il tuo primo tenant aziendale (es. Symbiotic, Qubitdata, Edilpi).
              </p>
              <button
                onClick={() => setShowNewOrgModal(true)}
                className="px-4 py-2 rounded-lg bg-accent-orange hover:bg-accent-orangeHover font-medium text-white text-sm"
              >
                Crea Organizzazione
              </button>
            </div>
          ) : (
            <>
              {activeTab === "tenants" && (
                <TenantSetup
                  currentOrg={currentOrg}
                  onOrgCreated={loadOrganizations}
                  onOrgUpdated={loadOrganizations}
                />
              )}
              {activeTab === "iam" && <DirectoryIAM currentOrg={currentOrg} />}
              {activeTab === "storage" && <StorageExplorer currentOrg={currentOrg} />}
              {activeTab === "delegation" && <DelegationBuilder currentOrg={currentOrg} />}
              {activeTab === "approvals" && <ApprovalHub currentOrg={currentOrg} />}
              {activeTab === "connect" && <Org3Connect currentOrg={currentOrg} />}
            </>
          )}
        </main>
      </div>

      {/* Modal Nuova Organizzazione */}
      {showNewOrgModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Nuova Organizzazione Aziendale</h3>
              <button onClick={() => setShowNewOrgModal(false)} className="text-xs text-neutral-500 hover:text-neutral-300">
                Chiudi
              </button>
            </div>

            <form onSubmit={handleCreateOrg} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Ragione Sociale / Nome</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => {
                    setNewName(e.target.value);
                    if (!newSlug) {
                      setNewSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, ""));
                    }
                  }}
                  placeholder="es. Qubitdata, Symbiotic, Edilpi"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Slug URL-Safe (Tenant ID)</label>
                <input
                  type="text"
                  required
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  placeholder="es. qubitdata"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white font-mono focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Owner Email</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Piano Iniziale</label>
                <select
                  value={newPlan}
                  onChange={(e) => setNewPlan(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange font-mono"
                >
                  <option value="business">business (Storage Cloud + HITL)</option>
                  <option value="free">free (Open Source base)</option>
                  <option value="enterprise">enterprise (Holding God Mode)</option>
                </select>
              </div>

              <div className="pt-3 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowNewOrgModal(false)}
                  className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-neutral-200 text-xs"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover text-white text-xs font-medium"
                >
                  Crea Organizzazione
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
