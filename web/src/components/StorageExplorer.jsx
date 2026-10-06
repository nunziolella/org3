import React, { useState, useEffect } from "react";
import {
  HardDrive,
  Folder,
  FileText,
  Upload,
  Trash2,
  Download,
  Eye,
  RefreshCw,
  ShieldCheck,
  Zap,
  CheckCircle2,
  AlertCircle,
  FileCode,
} from "lucide-react";
import { api } from "../api/client";

export function StorageExplorer({ currentOrg }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWs, setSelectedWs] = useState(null);
  const [domains, setDomains] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState("01_CORPORATE");
  const [items, setItems] = useState([]);
  const [cacheStats, setCacheStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // File Preview modal
  const [previewItem, setPreviewItem] = useState(null);
  const [previewContent, setPreviewContent] = useState("");

  // Upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFilename, setUploadFilename] = useState("");
  const [uploadFileContentB64, setUploadFileContentB64] = useState("");
  const [uploadMimeType, setUploadMimeType] = useState("text/plain");

  // Load Workspaces & Canonical Domains
  useEffect(() => {
    const init = async () => {
      if (!currentOrg?.id) return;
      try {
        const [wsList, canonData, cStats] = await Promise.all([
          api.organizations.listWorkspaces(currentOrg.id),
          api.storage.getCanonicalDomains(),
          api.storage.getCacheStats(),
        ]);
        setWorkspaces(wsList || []);
        if (wsList && wsList.length > 0) {
          const primary = wsList.find((w) => w.is_primary) || wsList[0];
          setSelectedWs(primary);
        }
        setDomains(canonData.domains || []);
        setCacheStats(cStats);
      } catch (err) {
        setError("Errore caricamento dati storage: " + err.message);
      }
    };
    init();
  }, [currentOrg?.id]);

  // Load items when selectedWs or selectedDomain changes
  const loadDomainItems = async (forceRefresh = false) => {
    if (!selectedWs?.id || !selectedDomain) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.storage.listItems(selectedWs.id, selectedDomain, { forceRefresh });
      setItems(data || []);
      const cStats = await api.storage.getCacheStats();
      setCacheStats(cStats);
    } catch (err) {
      setError("Impossibile caricare i file del dominio: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDomainItems();
  }, [selectedWs?.id, selectedDomain]);

  // Handle local file selection for upload
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadFilename(file.name);
    setUploadMimeType(file.type || "application/octet-stream");

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64String = event.target.result.split(",")[1];
      setUploadFileContentB64(base64String);
    };
    reader.readAsDataURL(file);
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedWs?.id || !uploadFileContentB64) return;

    setError(null);
    setSuccess(null);
    try {
      await api.storage.uploadItem(selectedWs.id, selectedDomain, {
        filename: uploadFilename,
        content_base64: uploadFileContentB64,
        mime_type: uploadMimeType,
      });

      setSuccess(`File "${uploadFilename}" caricato nel dominio ${selectedDomain}!`);
      setShowUploadModal(false);
      setUploadFilename("");
      setUploadFileContentB64("");
      loadDomainItems(true);
    } catch (err) {
      setError("Errore upload file: " + err.message);
    }
  };

  const handlePreview = async (item) => {
    setError(null);
    try {
      const res = await api.storage.readContent(selectedWs.id, item.item_id);
      setPreviewItem(item);
      setPreviewContent(res.text_content || `[Contenuto Binario ${res.size_bytes} byte - Base64: ${res.content_base64.substring(0, 100)}...]`);
    } catch (err) {
      setError("Errore apertura anteprima: " + err.message);
    }
  };

  const handleDelete = async (item) => {
    if (!confirm(`Sei sicuro di voler eliminare ${item.name}?`)) return;
    setError(null);
    try {
      await api.storage.deleteItem(selectedWs.id, item.item_id);
      setSuccess(`File "${item.name}" eliminato con successo.`);
      loadDomainItems(true);
    } catch (err) {
      setError("Errore cancellazione: " + err.message);
    }
  };

  const handleInvalidateCache = async () => {
    if (!selectedWs?.id) return;
    try {
      await api.storage.invalidateCache(selectedWs.id, selectedDomain);
      setSuccess(`Cache del dominio ${selectedDomain} invalidata.`);
      loadDomainItems(true);
    } catch (err) {
      setError("Errore invalidazione cache: " + err.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header & Anti-Quota Shield Stats */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <HardDrive className="w-7 h-7 text-accent-orange" />
            <span>10 Domini Persistenti & Anti-Quota Shield</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Architettura storage sovrana: partizione semantica a 10 domini e caching TTL 5m per azzerare rate-limit 429.
          </p>
        </div>

        {/* Shield Stats Card */}
        {cacheStats && (
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-dark-900 border border-dark-700 text-xs font-mono">
            <div className="flex items-center gap-2 text-accent-emerald">
              <ShieldCheck className="w-4 h-4" />
              <span>Shield: ATTIVO</span>
            </div>
            <div className="h-4 w-px bg-dark-700" />
            <div className="text-neutral-400">
              Hit Ratio: <span className="text-white font-bold">{cacheStats.hit_ratio_percent}%</span>
            </div>
            <div className="h-4 w-px bg-dark-700" />
            <div className="text-neutral-400">
              Chiamate Evitate: <span className="text-accent-orange font-bold">{cacheStats.anti_quota_saves}</span>
            </div>
            <div className="h-4 w-px bg-dark-700" />
            <div className="text-neutral-500 text-[10px]">TTL 300s</div>
          </div>
        )}
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

      {/* Workspace Selector Bar */}
      <div className="flex items-center justify-between p-3 bg-dark-900 rounded-lg border border-dark-700 text-xs">
        <div className="flex items-center gap-3">
          <span className="text-neutral-400 font-mono uppercase">Workspace Storage:</span>
          <select
            value={selectedWs?.id || ""}
            onChange={(e) => {
              const ws = workspaces.find((w) => w.id === e.target.value);
              if (ws) setSelectedWs(ws);
            }}
            className="bg-dark-800 text-white border border-dark-700 rounded px-2.5 py-1 focus:outline-none focus:border-accent-orange font-medium"
          >
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name} ({w.storage_provider}) {w.is_primary ? "★ Primario" : ""}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadDomainItems(true)}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-dark-800 hover:bg-dark-750 text-neutral-300 border border-dark-700"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Ricarica</span>
          </button>
          <button
            onClick={handleInvalidateCache}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-dark-800 hover:bg-dark-750 text-accent-orange border border-dark-700"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Invalida Cache</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-accent-orange hover:bg-accent-orangeHover text-white font-medium shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Carica File</span>
          </button>
        </div>
      </div>

      {/* Two Column Layout: Domains List & File Explorer */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left: 10 Persistent Domains */}
        <div className="space-y-2">
          <div className="text-xs font-mono uppercase text-neutral-400 font-semibold px-2 mb-2">
            Domini Persistenti (10)
          </div>

          {domains.map((dom) => {
            const isSelected = selectedDomain === dom.name;
            return (
              <button
                key={dom.name}
                onClick={() => setSelectedDomain(dom.name)}
                className={`w-full text-left p-3 rounded-xl border transition flex items-center justify-between ${
                  isSelected
                    ? "bg-dark-800 border-accent-orange text-white shadow-sm"
                    : "bg-dark-900 border-dark-700 text-neutral-400 hover:border-dark-600 hover:text-neutral-200"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Folder
                    className={`w-4 h-4 ${
                      isSelected ? "text-accent-orange fill-accent-orange/20" : "text-neutral-500"
                    }`}
                  />
                  <div>
                    <div className="text-xs font-bold leading-tight">{dom.name}</div>
                    <div className="text-[10px] text-neutral-500 leading-tight mt-0.5 line-clamp-1">{dom.title}</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Right: Files Table */}
        <div className="md:col-span-3 bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-dark-700">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2 font-mono">
                <Folder className="w-4 h-4 text-accent-orange" />
                <span>{selectedDomain}</span>
              </h2>
              <p className="text-xs text-neutral-400 mt-0.5">
                {domains.find((d) => d.name === selectedDomain)?.description || "File e cartelle persistenti del dominio."}
              </p>
            </div>

            <div className="text-xs font-mono text-neutral-500">
              {items.length} {items.length === 1 ? "elemento" : "elementi"}
            </div>
          </div>

          {loading ? (
            <div className="py-12 text-center text-neutral-500 text-xs font-mono flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Lettura dallo storage cloud in corso...</span>
            </div>
          ) : items.length === 0 ? (
            <div className="py-12 text-center space-y-3">
              <FileText className="w-8 h-8 text-neutral-600 mx-auto" />
              <div className="text-xs text-neutral-400">Nessun file presente in questo dominio.</div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="px-3 py-1.5 rounded-md bg-dark-800 text-xs text-neutral-300 hover:text-white border border-dark-700"
              >
                Carica il primo documento
              </button>
            </div>
          ) : (
            <div className="divide-y divide-dark-800">
              {items.map((item) => (
                <div key={item.item_id} className="py-3 flex items-center justify-between hover:bg-dark-850 px-2 rounded-lg transition">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-dark-800 border border-dark-700 flex items-center justify-center text-neutral-300">
                      {item.is_directory ? <Folder className="w-4 h-4 text-amber-500" /> : <FileCode className="w-4 h-4 text-cyan-400" />}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white">{item.name}</div>
                      <div className="text-[10px] text-neutral-500 font-mono flex items-center gap-2 mt-0.5">
                        <span>{(item.size_bytes / 1024).toFixed(1)} KB</span>
                        <span>·</span>
                        <span>{new Date(item.modified_time).toLocaleString()}</span>
                        {item.sha256_hash && (
                          <>
                            <span>·</span>
                            <span className="text-[9px] text-neutral-600">SHA: {item.sha256_hash.substring(0, 8)}...</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {!item.is_directory && (
                      <button
                        onClick={() => handlePreview(item)}
                        className="p-1.5 rounded hover:bg-dark-750 text-neutral-400 hover:text-white"
                        title="Visualizza anteprima"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(item)}
                      className="p-1.5 rounded hover:bg-red-950/60 text-neutral-500 hover:text-red-400"
                      title="Elimina"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* File Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] flex flex-col space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-dark-700">
              <div>
                <h3 className="text-sm font-bold font-mono text-white">{previewItem.name}</h3>
                <div className="text-xs text-neutral-500 font-mono mt-0.5">Percorso: {previewItem.path}</div>
              </div>
              <button onClick={() => setPreviewItem(null)} className="text-xs text-neutral-400 hover:text-white">
                Chiudi
              </button>
            </div>

            <div className="flex-1 overflow-auto bg-dark-950 p-4 rounded-lg border border-dark-800 font-mono text-xs text-neutral-200 whitespace-pre-wrap">
              {previewContent}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreviewItem(null)}
                className="px-4 py-1.5 rounded-md bg-dark-800 text-xs text-neutral-300 hover:text-white"
              >
                Chiudi Anteprima
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Carica nel Dominio: {selectedDomain}</h3>
              <button onClick={() => setShowUploadModal(false)} className="text-xs text-neutral-500 hover:text-neutral-300">
                Chiudi
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Seleziona File dal Disco</label>
                <input
                  type="file"
                  required
                  onChange={handleFileSelect}
                  className="w-full text-xs text-neutral-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-dark-800 file:text-neutral-200 hover:file:bg-dark-700 cursor-pointer"
                />
              </div>

              {uploadFilename && (
                <div className="p-3 bg-dark-850 rounded-lg border border-dark-800 text-xs font-mono text-neutral-300 space-y-1">
                  <div>Nome: <span className="text-white font-bold">{uploadFilename}</span></div>
                  <div>Tipo: <span className="text-neutral-400">{uploadMimeType}</span></div>
                </div>
              )}

              <div className="pt-3 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-neutral-200 text-xs"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  disabled={!uploadFileContentB64}
                  className="px-4 py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover disabled:opacity-50 text-white text-xs font-medium"
                >
                  Conferma e Carica
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
