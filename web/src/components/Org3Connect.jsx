import React, { useState, useEffect } from "react";
import {
  KeyRound,
  Plus,
  Copy,
  Check,
  ShieldCheck,
  Cpu,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  Search,
} from "lucide-react";
import { api } from "../api/client";

export function Org3Connect({ currentOrg }) {
  const [tokens, setTokens] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New Token Modal
  const [showModal, setShowModal] = useState(false);
  const [tokenName, setTokenName] = useState("");
  const [tokenMemberId, setTokenMemberId] = useState("");
  const [scopes, setScopes] = useState(["read", "write", "governance"]);

  // Show created token modal
  const [newRawToken, setNewRawToken] = useState(null);
  const [copied, setCopied] = useState(false);

  // Validate Token Tester
  const [testTokenInput, setTestTokenInput] = useState("");
  const [validationResult, setValidationResult] = useState(null);
  const [validating, setValidating] = useState(false);

  const loadData = async () => {
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const [tList, mList] = await Promise.all([
        api.tokens.list(currentOrg.id),
        api.members.list(currentOrg.id),
      ]);
      setTokens(tList || []);
      setMembers(mList || []);
      if (mList?.length > 0) setTokenMemberId(mList[0].id);
    } catch (err) {
      setError("Errore caricamento token: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentOrg?.id]);

  const handleCreateToken = async (e) => {
    e.preventDefault();
    if (!currentOrg?.id || !tokenMemberId) return;

    setError(null);
    setSuccess(null);
    try {
      const res = await api.tokens.create({
        org_id: currentOrg.id,
        member_id: tokenMemberId,
        name: tokenName,
        allowed_scopes: scopes,
      });

      setNewRawToken(res.token);
      setShowModal(false);
      setTokenName("");
      loadData();
    } catch (err) {
      setError("Errore generazione token: " + err.message);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRevoke = async (tokenId) => {
    if (!confirm("Sei sicuro di voler revocare questo token API? L'accesso per il client verrà interrotto.")) return;
    try {
      await api.tokens.revoke(tokenId);
      setSuccess("Token API revocato.");
      loadData();
    } catch (err) {
      setError("Errore revoca: " + err.message);
    }
  };

  const handleValidateToken = async (e) => {
    e.preventDefault();
    if (!testTokenInput.trim()) return;

    setValidating(true);
    setValidationResult(null);
    try {
      const res = await api.tokens.validate(testTokenInput.trim());
      setValidationResult({ valid: true, data: res });
    } catch (err) {
      setValidationResult({ valid: false, error: err.message });
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <KeyRound className="w-7 h-7 text-accent-orange" />
            <span>Org3 Connect Gateway & Tool Tokens</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Gestione token API crittografici SHA-256 e integrazione universale con Structura OS, Memograph e client MCP esterni.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-orange hover:bg-accent-orangeHover text-white font-medium text-sm transition shadow-lg shadow-accent-orange/20"
        >
          <Plus className="w-4 h-4" />
          <span>Genera Token API</span>
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

      {/* Connected Tools Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-dark-900 border border-dark-700 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-neutral-400 font-semibold">Execution Tool</span>
            <span className="w-2 h-2 rounded-full bg-accent-emerald animate-ping" />
          </div>
          <div className="text-base font-bold text-white">Structura OS</div>
          <p className="text-xs text-neutral-400">Piattaforma operativa e gestionale: preventivi, PRD, work management.</p>
          <div className="pt-2 text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Connesso a cuprite.godigix.com</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-dark-900 border border-dark-700 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-neutral-400 font-semibold">Knowledge Fabric</span>
            <span className="w-2 h-2 rounded-full bg-accent-emerald animate-ping" />
          </div>
          <div className="text-base font-bold text-white">Memograph Engine</div>
          <p className="text-xs text-neutral-400">Memoria a 3 livelli, grafo ontologico Neo4j e vettorizzazione continua.</p>
          <div className="pt-2 text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Connesso a memory.godigix.com</span>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-dark-900 border border-dark-700 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-neutral-400 font-semibold">Universal MCP</span>
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          </div>
          <div className="text-base font-bold text-white">FastMCP Gateway</div>
          <p className="text-xs text-neutral-400">Endpoint per Claude Desktop, Cursor e agenti LLM esterni.</p>
          <div className="pt-2 text-[11px] font-mono text-cyan-400 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" />
            <span>https://mcp.org3.ai/{currentOrg?.slug}</span>
          </div>
        </div>
      </div>

      {/* Tokens List & Tester Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Active Tokens (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-accent-orange" />
            <span>Token API Attivi ({tokens.length})</span>
          </h2>

          {tokens.length === 0 ? (
            <div className="p-8 text-center rounded-xl bg-dark-900 border border-dark-700 space-y-2">
              <KeyRound className="w-8 h-8 text-neutral-600 mx-auto" />
              <div className="text-sm text-neutral-400">Nessun token API generato per questa organizzazione.</div>
            </div>
          ) : (
            <div className="space-y-3">
              {tokens.map((tok) => {
                const holder = members.find((m) => m.id === tok.member_id);
                return (
                  <div
                    key={tok.id}
                    className="p-4 rounded-xl bg-dark-900 border border-dark-700 flex items-center justify-between hover:border-dark-600 transition"
                  >
                    <div className="space-y-1">
                      <div className="font-bold text-white text-sm flex items-center gap-2">
                        <span>{tok.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-800 text-neutral-400 border border-dark-700">
                          {tok.token_hash.substring(0, 10)}...
                        </span>
                      </div>
                      <div className="text-xs text-neutral-400 font-mono">
                        Assegnato a: <span className="text-neutral-200">{holder?.name || tok.member_id}</span> ({holder?.role})
                      </div>
                      <div className="flex gap-1.5 pt-1">
                        {tok.allowed_scopes?.map((s) => (
                          <span
                            key={s}
                            className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-dark-850 text-neutral-400 border border-dark-800"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={() => handleRevoke(tok.id)}
                      className="p-2 rounded-lg hover:bg-red-950/60 text-neutral-500 hover:text-red-400 transition"
                      title="Revoca token"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Token Validator Sandbox (1 col) */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-accent-emerald" />
            <span>Validatore Token Live</span>
          </h2>
          <p className="text-xs text-neutral-400">
            Simula l'interrogazione di validazione eseguita da Structura o da un client MCP al momento dell'autenticazione.
          </p>

          <form onSubmit={handleValidateToken} className="space-y-3">
            <div>
              <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Bearer Token (org3_sk_...)</label>
              <input
                type="text"
                value={testTokenInput}
                onChange={(e) => setTestTokenInput(e.target.value)}
                placeholder="Incolla il token qui..."
                className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-xs font-mono text-white focus:outline-none focus:border-accent-orange"
              />
            </div>

            <button
              type="submit"
              disabled={validating || !testTokenInput.trim()}
              className="w-full py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover text-white text-xs font-medium transition disabled:opacity-50"
            >
              {validating ? "Verifica in corso..." : "Verifica Token"}
            </button>
          </form>

          {validationResult && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono space-y-1 ${
                validationResult.valid
                  ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                  : "bg-red-950/40 border-red-800 text-red-300"
              }`}
            >
              <div className="font-bold flex items-center gap-1.5">
                {validationResult.valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span>{validationResult.valid ? "TOKEN VALIDO & ATTIVO" : "TOKEN NON VALIDO / REVOCATO"}</span>
              </div>
              {validationResult.valid && (
                <div className="text-[11px] opacity-90 pt-1 space-y-0.5">
                  <div>Membro: {validationResult.data?.member?.name}</div>
                  <div>Ruolo: {validationResult.data?.member?.role}</div>
                  <div>God Mode: {validationResult.data?.member?.is_master ? "SI" : "NO"}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal Nuovo Token */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Genera Nuovo Token API Org3</h3>
              <button onClick={() => setShowModal(false)} className="text-xs text-neutral-500 hover:text-neutral-300">
                Chiudi
              </button>
            </div>

            <form onSubmit={handleCreateToken} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Nome del Token / Servizio</label>
                <input
                  type="text"
                  required
                  value={tokenName}
                  onChange={(e) => setTokenName(e.target.value)}
                  placeholder="es. Structura Platform Connector"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Membro Associato</label>
                <select
                  value={tokenMemberId}
                  onChange={(e) => setTokenMemberId(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                >
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.role})
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-neutral-200 text-xs"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover text-white text-xs font-medium"
                >
                  Genera Token
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Raw Token Shown Once Modal */}
      {newRawToken && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-accent-orange/60 rounded-xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
            <div className="flex items-center gap-2 text-accent-orange">
              <KeyRound className="w-5 h-5" />
              <h3 className="text-base font-bold">Copia il Token API appena generato</h3>
            </div>

            <p className="text-xs text-neutral-300">
              Per motivi di sicurezza, questo valore in chiaro viene mostrato **SOLO ORA**. Non potrà essere visualizzato di nuovo (nel database viene salvato solo l'hash crittografico SHA-256).
            </p>

            <div className="p-3 bg-dark-950 rounded-lg border border-dark-800 flex items-center justify-between gap-2">
              <span className="font-mono text-xs text-accent-emerald break-all select-all">{newRawToken}</span>
              <button
                onClick={() => handleCopy(newRawToken)}
                className="px-3 py-1.5 rounded bg-dark-800 hover:bg-dark-700 text-xs font-medium text-white flex items-center gap-1.5 shrink-0"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-accent-emerald" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copiato!" : "Copia"}</span>
              </button>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setNewRawToken(null)}
                className="px-4 py-2 rounded-md bg-accent-orange text-white text-xs font-medium"
              >
                Ho salvato il Token
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
