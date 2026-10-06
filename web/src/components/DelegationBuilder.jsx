import React, { useState, useEffect } from "react";
import {
  Scale,
  Plus,
  ShieldAlert,
  ShieldCheck,
  Ban,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { api } from "../api/client";

export function DelegationBuilder({ currentOrg }) {
  const [policies, setPolicies] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New Policy Form
  const [showModal, setShowModal] = useState(false);
  const [actorId, setActorId] = useState("");
  const [policyName, setPolicyName] = useState("");
  const [scope, setScope] = useState("quotes");
  const [maxAmount, setMaxAmount] = useState(5000);
  const [gate, setGate] = useState("CLASS_C");
  const [constraints, setConstraints] = useState([
    "NO_IP_CONCESSION",
    "NO_EXCLUSIVITY",
    "NO_ROADMAP_COMMITMENT",
  ]);

  // Simulator / Sandbox state
  const [simActorId, setSimActorId] = useState("");
  const [simAction, setSimAction] = useState("issue_quote");
  const [simAmount, setSimAmount] = useState(4500);
  const [simTouchesIp, setSimTouchesIp] = useState(false);
  const [simExclusivity, setSimExclusivity] = useState(false);
  const [simRoadmap, setSimRoadmap] = useState(false);
  const [simDiscount, setSimDiscount] = useState(5);
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const [pList, mList] = await Promise.all([
        api.delegation.list(currentOrg.id),
        api.members.list(currentOrg.id),
      ]);
      setPolicies(pList || []);
      setMembers(mList || []);
      if (mList?.length > 0) {
        setActorId(mList[0].id);
        setSimActorId(mList[0].id);
      }
    } catch (err) {
      setError("Errore caricamento contratti di delega: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentOrg?.id]);

  const toggleConstraint = (item) => {
    if (constraints.includes(item)) {
      setConstraints(constraints.filter((c) => c !== item));
    } else {
      setConstraints([...constraints, item]);
    }
  };

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    if (!currentOrg?.id || !actorId) return;

    setError(null);
    setSuccess(null);
    try {
      await api.delegation.create(currentOrg.id, {
        actor_id: actorId,
        name: policyName,
        scope,
        max_financial_authority: parseFloat(maxAmount),
        constraints,
        approval_gate: gate,
      });

      setSuccess(`Contratto di delega "${policyName}" registrato con successo!`);
      setShowModal(false);
      setPolicyName("");
      setMaxAmount(5000);
      loadData();
    } catch (err) {
      setError("Errore creazione contratto di delega: " + err.message);
    }
  };

  const handleRevokePolicy = async (policyId) => {
    if (!confirm("Sei sicuro di voler revocare questa delega?")) return;
    try {
      await api.delegation.revoke(policyId);
      setSuccess("Contratto di delega revocato.");
      loadData();
    } catch (err) {
      setError("Errore revoca delega: " + err.message);
    }
  };

  const handleSimulateAction = async (e) => {
    e.preventDefault();
    if (!currentOrg?.id || !simActorId) return;

    setSimulating(true);
    setError(null);
    setSimResult(null);

    try {
      const res = await api.delegation.evaluateDryRun({
        org_id: currentOrg.id,
        actor_id: simActorId,
        action: simAction,
        requested_amount: parseFloat(simAmount) || 0,
        touches_ip: simTouchesIp,
        grants_exclusivity: simExclusivity,
        commits_to_fixed_roadmap: simRoadmap,
        discount_percent: parseFloat(simDiscount) || 0,
      });

      setSimResult(res);
    } catch (err) {
      setError("Errore valutazione delega: " + err.message);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Scale className="w-7 h-7 text-accent-orange" />
            <span>Delegation Policy Builder & Guardiani Anti-Chrimat</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Modello dichiarativo dei contratti di delega condizionata e verifica real-time dei vincoli negativi inviolabili.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-orange hover:bg-accent-orangeHover text-white font-medium text-sm transition shadow-lg shadow-accent-orange/20"
        >
          <Plus className="w-4 h-4" />
          <span>Nuovo Contratto di Delega</span>
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

      {/* Two Column Layout: Policies List & Live Evaluator Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Active Policies (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-accent-emerald" />
              <span>Contratti di Delega Attivi ({policies.length})</span>
            </h2>
          </div>

          {policies.length === 0 ? (
            <div className="p-8 text-center rounded-xl bg-dark-900 border border-dark-700 space-y-3">
              <Scale className="w-8 h-8 text-neutral-600 mx-auto" />
              <div className="text-sm text-neutral-400">Nessun contratto di delega attivo.</div>
              <p className="text-xs text-neutral-500 max-w-sm mx-auto">
                Crea contratti con massimali di spesa e vincoli stringenti per delegare decisioni a umani o agenti AI in sicurezza.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {policies.map((p) => {
                const actor = members.find((m) => m.id === p.actor_id);
                return (
                  <div
                    key={p.id}
                    className="p-5 rounded-xl bg-dark-900 border border-dark-700 space-y-3 hover:border-dark-600 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-white text-base">{p.name}</div>
                        <div className="text-xs text-neutral-400 font-mono mt-0.5">
                          Attore: <span className="text-neutral-200 font-semibold">{actor?.name || p.actor_id}</span> ({actor?.member_type || "N/A"})
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-dark-800 text-neutral-300 border border-dark-700">
                          {p.scope}
                        </span>
                        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-accent-orange/15 text-accent-orange border border-accent-orange/30">
                          {p.approval_gate}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-dark-850 p-3 rounded-lg border border-dark-800">
                      <div>
                        <span className="text-neutral-500 block uppercase text-[10px]">Massimale Finanziario:</span>
                        <span className="text-white font-bold">€{parseFloat(p.max_financial_authority).toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block uppercase text-[10px]">Stato Contratto:</span>
                        <span className={p.is_revoked ? "text-red-400" : "text-emerald-400"}>
                          {p.is_revoked ? "REVOCATO" : "ATTIVO"}
                        </span>
                      </div>
                    </div>

                    {/* Negative Constraints Tags */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {p.constraints?.map((c) => (
                        <span
                          key={c}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/40 text-red-300 border border-red-900/60 flex items-center gap-1"
                        >
                          <Ban className="w-2.5 h-2.5" />
                          <span>{c}</span>
                        </span>
                      ))}
                    </div>

                    <div className="pt-2 flex justify-end">
                      {!p.is_revoked && (
                        <button
                          onClick={() => handleRevokePolicy(p.id)}
                          className="text-xs text-red-400 hover:text-red-300 underline font-mono"
                        >
                          Revoca Delega
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Live Policy Evaluation Sandbox (1 col) */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-dark-700">
            <Sparkles className="w-5 h-5 text-accent-orange" />
            <h2 className="text-base font-bold text-white">Policy Evaluator Sandbox</h2>
          </div>
          <p className="text-xs text-neutral-400">
            Testa in tempo reale se un'azione proposta viene approvata, respinta o instradata a un Gate HITL di Classe C/D.
          </p>

          <form onSubmit={handleSimulateAction} className="space-y-4 text-xs">
            <div>
              <label className="block text-neutral-400 font-mono uppercase mb-1">Attore Richiedente</label>
              <select
                value={simActorId}
                onChange={(e) => setSimActorId(e.target.value)}
                className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-white focus:outline-none focus:border-accent-orange"
              >
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.role}) {m.is_master ? "★ GOD MODE" : ""}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-neutral-400 font-mono uppercase mb-1">Azione Richiesta</label>
              <input
                type="text"
                value={simAction}
                onChange={(e) => setSimAction(e.target.value)}
                className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-white focus:outline-none focus:border-accent-orange"
              />
            </div>

            <div>
              <label className="block text-neutral-400 font-mono uppercase mb-1">Importo Economico (€)</label>
              <input
                type="number"
                value={simAmount}
                onChange={(e) => setSimAmount(e.target.value)}
                className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-white focus:outline-none focus:border-accent-orange"
              />
            </div>

            {/* Checkboxes for CHRIMAT traps */}
            <div className="p-3 bg-dark-850 rounded-lg border border-dark-800 space-y-2">
              <div className="font-mono uppercase text-[10px] text-neutral-500 font-bold mb-1">Condizioni a Rischio</div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simTouchesIp}
                  onChange={(e) => setSimTouchesIp(e.target.checked)}
                  className="rounded bg-dark-800 border-dark-700 text-accent-orange"
                />
                <span className="text-neutral-300">Cede Diritti di Proprietà Intellettuale (IP)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simExclusivity}
                  onChange={(e) => setSimExclusivity(e.target.checked)}
                  className="rounded bg-dark-800 border-dark-700 text-accent-orange"
                />
                <span className="text-neutral-300">Concede Clausola di Esclusiva</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simRoadmap}
                  onChange={(e) => setSimRoadmap(e.target.checked)}
                  className="rounded bg-dark-800 border-dark-700 text-accent-orange"
                />
                <span className="text-neutral-300">Impegna Roadmap Fissa Vincolante</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={simulating}
              className="w-full py-2.5 rounded-lg bg-accent-orange hover:bg-accent-orangeHover font-medium text-white flex items-center justify-center gap-2 shadow-lg shadow-accent-orange/20"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>{simulating ? "Valutazione..." : "Esegui Valutazione"}</span>
            </button>
          </form>

          {/* Verdict Box */}
          {simResult && (
            <div
              className={`p-4 rounded-xl border space-y-2 ${
                simResult.allowed
                  ? "bg-emerald-950/40 border-emerald-800 text-emerald-200"
                  : "bg-red-950/40 border-red-800 text-red-200"
              }`}
            >
              <div className="flex items-center justify-between font-mono font-bold text-sm">
                <span>VERDETTO: {simResult.allowed ? "AUTORIZZATO" : "BLOCCATO / GATE"}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-black/40 border border-current">
                  {simResult.governance_gate}
                </span>
              </div>

              <p className="text-xs opacity-90 leading-relaxed">{simResult.reason}</p>

              {simResult.requires_hitl && (
                <div className="text-[11px] font-mono text-amber-400 font-semibold pt-1">
                  ⚠️ Richiede approvazione formale Human-in-the-Loop!
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modal Nuovo Contratto */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-lg w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Nuovo Contratto di Delega</h3>
              <button onClick={() => setShowModal(false)} className="text-xs text-neutral-500 hover:text-neutral-300">
                Chiudi
              </button>
            </div>

            <form onSubmit={handleCreatePolicy} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Nome Politica / Contratto</label>
                <input
                  type="text"
                  required
                  value={policyName}
                  onChange={(e) => setPolicyName(e.target.value)}
                  placeholder="es. Delega Commerciale Offerte Mid-Market"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Attore Delegato</label>
                <select
                  value={actorId}
                  onChange={(e) => setActorId(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                >
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.member_type} - {m.role})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Ambito (Scope)</label>
                  <select
                    value={scope}
                    onChange={(e) => setScope(e.target.value)}
                    className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  >
                    <option value="quotes">Preventivi (quotes)</option>
                    <option value="purchasing">Acquisti (purchasing)</option>
                    <option value="roadmap">Roadmap & PRD</option>
                    <option value="deployments">Deploy & Release</option>
                    <option value="intellectual_property">Proprietà Intellettuale</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Tetto Massimo (€)</label>
                  <input
                    type="number"
                    required
                    value={maxAmount}
                    onChange={(e) => setMaxAmount(e.target.value)}
                    className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  />
                </div>
              </div>

              {/* Vincoli Negativi Inviolabili */}
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-2 font-bold text-accent-orange">
                  Vincoli Negativi Inviolabili (Lezione CHRIMAT)
                </label>
                <div className="space-y-2 p-3 bg-dark-850 rounded-lg border border-dark-800 text-xs">
                  {[
                    { id: "NO_IP_CONCESSION", label: "NO_IP_CONCESSION (Divieto cedere proprietà intellettuale)" },
                    { id: "NO_EXCLUSIVITY", label: "NO_EXCLUSIVITY (Divieto accordare clausole di esclusiva)" },
                    { id: "NO_ROADMAP_COMMITMENT", label: "NO_ROADMAP_COMMITMENT (Divieto impegni vincolanti a lungo termine)" },
                  ].map((c) => (
                    <label key={c.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={constraints.includes(c.id)}
                        onChange={() => toggleConstraint(c.id)}
                        className="rounded bg-dark-800 border-dark-700 text-accent-orange"
                      />
                      <span className="text-neutral-300">{c.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Gate di Rischio</label>
                <select
                  value={gate}
                  onChange={(e) => setGate(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-md p-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                >
                  <option value="CLASS_A">CLASS_A (Auto-Approve a rischio zero)</option>
                  <option value="CLASS_B">CLASS_B (Evidence-backed automatica)</option>
                  <option value="CLASS_C">CLASS_C (Human-in-the-Loop obbligatorio)</option>
                  <option value="CLASS_D">CLASS_D (Master Assoluto God Mode)</option>
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
                  Salva Contratto
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
