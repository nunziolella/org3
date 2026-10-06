import React, { useState, useEffect } from "react";
import {
  Building2,
  HardDrive,
  Plus,
  CheckCircle2,
  AlertCircle,
  FolderGit2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { api } from "../api/client";

export function TenantSetup({ currentOrg, onOrgCreated, onOrgUpdated }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New Workspace form state
  const [showWsModal, setShowWsModal] = useState(false);
  const [wsName, setWsName] = useState("");
  const [wsProvider, setWsProvider] = useState("google_drive");
  const [wsRootFolder, setWsRootFolder] = useState("");
  const [wsBucketName, setWsBucketName] = useState("");
  const [wsIsPrimary, setWsIsPrimary] = useState(true);

  // Load workspaces
  const loadWorkspaces = async () => {
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const data = await api.organizations.listWorkspaces(currentOrg.id);
      setWorkspaces(data || []);
    } catch (err) {
      setError("Impossibile caricare i workspace: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspaces();
  }, [currentOrg?.id]);

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!currentOrg?.id) return;

    setError(null);
    setSuccess(null);

    const storageConfig = {};
    if (wsProvider === "google_drive") {
      storageConfig.root_folder_id = wsRootFolder || "root";
      storageConfig.simulate = true; // Safe simulation mode by default
    } else if (wsProvider === "s3" || wsProvider === "r2") {
      storageConfig.bucket_name = wsBucketName || `org3-${currentOrg.slug}`;
      storageConfig.simulate = true;
    } else {
      storageConfig.base_path = `./storage_data/${currentOrg.slug}`;
    }

    try {
      await api.organizations.createWorkspace(currentOrg.id, {
        name: wsName,
        storage_provider: wsProvider,
        storage_config: storageConfig,
        is_primary: wsIsPrimary,
      });

      setSuccess(`Workspace "${wsName}" creato con successo!`);
      setShowWsModal(false);
      setWsName("");
      setWsRootFolder("");
      setWsBucketName("");
      loadWorkspaces();
    } catch (err) {
      setError("Errore nella creazione del workspace: " + err.message);
    }
  };

  const handleInitDomains = async (workspaceId) => {
    setError(null);
    try {
      await api.storage.initDomains(workspaceId);
      setSuccess("Tutti i 10 Domini Persistenti sono stati inizializzati e mappati nello storage!");
      loadWorkspaces();
    } catch (err) {
      setError("Errore inizializzazione domini: " + err.message);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Building2 className="w-7 h-7 text-accent-orange" />
            <span>Tenant & Cloud Storage Setup</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Configurazione del profilo aziendale, feature flags di billing e aggancio dello Storage Cloud sovereign.
          </p>
        </div>

        <button
          onClick={() => setShowWsModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-orange hover:bg-accent-orangeHover text-white font-medium text-sm transition shadow-lg shadow-accent-orange/20"
        >
          <Plus className="w-4 h-4" />
          <span>Nuovo Workspace Storage</span>
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-4 rounded-lg bg-emerald-950/50 border border-emerald-800 text-emerald-300 text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Company Profile Card */}
      {currentOrg && (
        <div className="p-6 rounded-xl bg-dark-900 border border-dark-700 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-dark-700">
            <div>
              <div className="text-xs uppercase font-mono text-neutral-400 font-semibold">Organizzazione Attiva</div>
              <div className="text-xl font-bold text-white mt-0.5">{currentOrg.name}</div>
              <div className="text-xs text-neutral-500 font-mono mt-0.5">Slug: {currentOrg.slug} · ID: {currentOrg.id}</div>
            </div>

            <div className="text-right">
              <div className="text-xs uppercase font-mono text-neutral-400">Owner & Admin</div>
              <div className="text-sm font-medium text-neutral-200">{currentOrg.owner_email}</div>
            </div>
          </div>

          {/* Billing via Feature Flags */}
          <div>
            <div className="text-xs uppercase font-mono text-neutral-400 mb-3 font-semibold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent-orange" />
              <span>Feature Flags di Abbonamento (Rollout Istantaneo)</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {["free", "business", "enterprise"].map((planName) => {
                const isCurrent = currentOrg.plan === planName;
                return (
                  <div
                    key={planName}
                    className={`p-4 rounded-lg border transition ${
                      isCurrent
                        ? "bg-dark-800 border-accent-orange shadow-md shadow-accent-orange/10"
                        : "bg-dark-850 border-dark-700 opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold uppercase font-mono text-white">{planName}</span>
                      {isCurrent && (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-accent-orange text-white">
                          ATTIVO
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-neutral-400 mt-2">
                      {planName === "free" && "Strumenti open-source, storage locale, nessun limite di utenti di prova."}
                      {planName === "business" && "Storage Cloud (Drive/S3), Guardiani anti-Chrimat, Notification Hub HITL."}
                      {planName === "enterprise" && "Multi-workspace illimitati, SLA dedicato, God Mode federato per holding."}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Workspaces & Storage Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-accent-emerald" />
            <span>Workspace di Lavoro & Connessione Storage</span>
          </h2>

          <button
            onClick={loadWorkspaces}
            className="text-xs font-mono text-neutral-400 hover:text-neutral-200 flex items-center gap-1.5 px-2.5 py-1 rounded bg-dark-800 border border-dark-700"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Aggiorna</span>
          </button>
        </div>

        {workspaces.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-dark-900 border border-dark-700 space-y-3">
            <FolderGit2 className="w-10 h-10 text-neutral-600 mx-auto" />
            <div className="text-sm font-medium text-neutral-300">Nessun Workspace di storage collegato</div>
            <p className="text-xs text-neutral-500 max-w-md mx-auto">
              Collega la cartella Google Drive dell'azienda o un bucket S3/Cloudflare R2 per mappare automaticamente i 10 domini persistenti.
            </p>
            <button
              onClick={() => setShowWsModal(true)}
              className="mt-2 px-3 py-1.5 rounded-md bg-dark-800 hover:bg-dark-700 border border-dark-600 text-xs font-medium text-neutral-200"
            >
              Crea il Primo Workspace
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                className="p-5 rounded-xl bg-dark-900 border border-dark-700 flex flex-col justify-between hover:border-dark-600 transition"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{ws.name}</span>
                      {ws.is_primary && (
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 font-semibold">
                          Primario
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-dark-800 text-neutral-400 border border-dark-700">
                      {ws.storage_provider}
                    </span>
                  </div>

                  <div className="text-xs text-neutral-400 font-mono space-y-1 bg-dark-850 p-3 rounded-lg border border-dark-800">
                    <div>ID: {ws.id}</div>
                    <div>Root Ref: {ws.storage_config?.root_folder_id || ws.storage_config?.bucket_name || ws.storage_config?.base_path || "N/A"}</div>
                    <div>Modalità: {ws.storage_config?.simulate ? "Simulation/Mock Shield" : "Live Production"}</div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-dark-800 flex items-center justify-between">
                  <span className="text-xs text-neutral-500">10 Domini Persistenti</span>
                  <button
                    onClick={() => handleInitDomains(ws.id)}
                    className="px-3 py-1 rounded bg-dark-800 hover:bg-dark-700 border border-dark-700 text-xs font-medium text-neutral-200 transition"
                  >
                    Inizializza Domini
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Nuovo Workspace */}
      {showWsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-lg w-full space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Nuovo Workspace Storage</h3>
              <button
                onClick={() => setShowWsModal(false)}
                className="text-neutral-500 hover:text-neutral-300 text-sm"
              >
                Chiudi
              </button>
            </div>

            <form onSubmit={handleCreateWorkspace} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Nome Workspace</label>
                <input
                  type="text"
                  required
                  value={wsName}
                  onChange={(e) => setWsName(e.target.value)}
                  placeholder="es. Main Drive Qubitdata"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Provider Cloud</label>
                <select
                  value={wsProvider}
                  onChange={(e) => setWsProvider(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                >
                  <option value="google_drive">Google Drive (Service Account / OAuth)</option>
                  <option value="s3">AWS S3</option>
                  <option value="r2">Cloudflare R2</option>
                  <option value="local_fs">Filesystem Locale</option>
                </select>
              </div>

              {wsProvider === "google_drive" && (
                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">ID Cartella Radice (Root Folder ID)</label>
                  <input
                    type="text"
                    value={wsRootFolder}
                    onChange={(e) => setWsRootFolder(e.target.value)}
                    placeholder="es. 1A2b3C_XYZ... (lascia vuoto per default)"
                    className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  />
                  <p className="text-[11px] text-neutral-500 mt-1">Sotto questa cartella verranno mappati i 10 domini (01_CORPORATE, ecc.).</p>
                </div>
              )}

              {(wsProvider === "s3" || wsProvider === "r2") && (
                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Nome Bucket</label>
                  <input
                    type="text"
                    value={wsBucketName}
                    onChange={(e) => setWsBucketName(e.target.value)}
                    placeholder="es. org3-company-vault"
                    className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  />
                </div>
              )}

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="primaryWs"
                  checked={wsIsPrimary}
                  onChange={(e) => setWsIsPrimary(e.target.checked)}
                  className="rounded bg-dark-800 border-dark-700 text-accent-orange focus:ring-0"
                />
                <label htmlFor="primaryWs" className="text-xs text-neutral-300">
                  Imposta come Workspace Primario
                </label>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowWsModal(false)}
                  className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-neutral-200 text-sm"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover text-white text-sm font-medium"
                >
                  Salva Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
