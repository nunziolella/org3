import React, { useState, useEffect } from "react";
import {
  BellRing,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Send,
  MessageSquare,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { api } from "../api/client";

export function ApprovalHub({ currentOrg }) {
  const [approvals, setApprovals] = useState([]);
  const [filterStatus, setFilterStatus] = useState("PENDING");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Reject modal state
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectNote, setRejectNote] = useState("");

  const loadApprovals = async () => {
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const statusParam = filterStatus === "ALL" ? null : filterStatus;
      const data = await api.approvals.list(currentOrg.id, statusParam);
      setApprovals(data || []);
    } catch (err) {
      setError("Errore caricamento richieste HITL: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, [currentOrg?.id, filterStatus]);

  const handleResolve = async (approvalId, action, note = "") => {
    setError(null);
    setSuccess(null);
    try {
      await api.approvals.resolve(approvalId, {
        action,
        resolution_note: note || (action === "APPROVED" ? "Approvato via Org3 Control Plane Web" : "Rifiutato"),
      });

      setSuccess(`Richiesta ${action === "APPROVED" ? "approvata" : "respinta"} con successo!`);
      setRejectingId(null);
      setRejectNote("");
      loadApprovals();
    } catch (err) {
      setError("Errore nella risoluzione: " + err.message);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <BellRing className="w-7 h-7 text-accent-orange" />
            <span>Notification & Approval Hub (Human-in-the-Loop)</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Cabina di regia centralizzata per richieste di autorizzazione generate da Structura, Memograph o client MCP esterni.
          </p>
        </div>

        {/* Telegram Webhook Deep-Link Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-900 border border-dark-700 text-xs font-mono text-neutral-300">
          <Send className="w-3.5 h-3.5 text-cyan-400" />
          <span>Telegram Webhook: <strong className="text-accent-emerald">Connesso (@StructuraBot)</strong></span>
        </div>
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

      {/* Status Filter Bar */}
      <div className="flex items-center justify-between bg-dark-900 p-4 rounded-xl border border-dark-700">
        <div className="flex items-center gap-2">
          {["PENDING", "APPROVED", "REJECTED", "ALL"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono uppercase transition ${
                filterStatus === st
                  ? "bg-accent-orange text-white shadow-sm"
                  : "bg-dark-800 text-neutral-400 hover:text-white"
              }`}
            >
              {st === "PENDING" && "In Sospeso (Pending)"}
              {st === "APPROVED" && "Approvate"}
              {st === "REJECTED" && "Respinte"}
              {st === "ALL" && "Tutte"}
            </button>
          ))}
        </div>

        <button
          onClick={loadApprovals}
          className="p-2 rounded-md bg-dark-800 border border-dark-700 text-neutral-400 hover:text-white transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Approvals List */}
      {loading ? (
        <div className="py-16 text-center text-neutral-500 font-mono text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Caricamento richieste HITL...</span>
        </div>
      ) : approvals.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-dark-900 border border-dark-700 space-y-3">
          <CheckCircle2 className="w-10 h-10 text-accent-emerald mx-auto" />
          <div className="text-sm font-bold text-white">Nessuna richiesta in questa categoria</div>
          <p className="text-xs text-neutral-500">Tutti i gate operativi e contratti di delega sono allineati.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((req) => (
            <div
              key={req.id}
              className={`p-6 rounded-xl border transition space-y-4 ${
                req.status === "PENDING"
                  ? "bg-dark-900 border-accent-orange/40 shadow-lg shadow-accent-orange/5"
                  : "bg-dark-900/60 border-dark-700"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                        req.risk_class === "D"
                          ? "bg-accent-orange/15 text-accent-orange border-accent-orange/40"
                          : req.risk_class === "C"
                          ? "bg-amber-950 text-amber-400 border-amber-800"
                          : "bg-blue-950 text-blue-400 border-blue-800"
                      }`}
                    >
                      CLASSE {req.risk_class}
                    </span>
                    <span className="text-xs font-mono text-neutral-400 uppercase">Da: {req.source_service}</span>
                    <span className="text-xs text-neutral-600">·</span>
                    <span className="text-xs text-neutral-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(req.created_at).toLocaleString()}</span>
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mt-1.5">{req.title}</h3>
                  <p className="text-xs text-neutral-300 mt-0.5">{req.description}</p>
                </div>

                <div>
                  <span
                    className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full ${
                      req.status === "APPROVED"
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                        : req.status === "REJECTED"
                        ? "bg-red-950 text-red-300 border border-red-800"
                        : "bg-amber-950 text-amber-300 border border-amber-800 animate-pulse"
                    }`}
                  >
                    {req.status}
                  </span>
                </div>
              </div>

              {/* Payload Diff Box */}
              {req.payload && Object.keys(req.payload).length > 0 && (
                <div className="p-3 bg-dark-950 rounded-lg border border-dark-800 text-xs font-mono text-neutral-300">
                  <div className="text-[10px] uppercase font-bold text-neutral-500 mb-1">Payload Dettagliato:</div>
                  <pre className="overflow-x-auto whitespace-pre-wrap">{JSON.stringify(req.payload, null, 2)}</pre>
                </div>
              )}

              {/* Resolution Note if resolved */}
              {req.resolution_note && (
                <div className="text-xs text-neutral-400 bg-dark-850 p-2.5 rounded border border-dark-800 flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
                  <span>Nota di risoluzione: <strong className="text-neutral-200">{req.resolution_note}</strong></span>
                </div>
              )}

              {/* Action Buttons for Pending */}
              {req.status === "PENDING" && (
                <div className="pt-2 border-t border-dark-800 flex items-center justify-end gap-3">
                  <button
                    onClick={() => setRejectingId(req.id)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-200 text-xs font-medium transition"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Rifiuta con Nota</span>
                  </button>
                  <button
                    onClick={() => handleResolve(req.id, "APPROVED")}
                    className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-accent-emerald hover:bg-emerald-600 text-white text-xs font-bold transition shadow-lg shadow-emerald-900/30"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approva (1-Click)</span>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Reject Modal */}
      {rejectingId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Motivazione del Rifiuto</h3>
            <textarea
              rows={4}
              value={rejectNote}
              onChange={(e) => setRejectNote(e.target.value)}
              placeholder="Inserisci la motivazione che verrà notificata all'agente o al richiedente..."
              className="w-full bg-dark-800 border border-dark-700 rounded-md p-3 text-xs text-white focus:outline-none focus:border-accent-orange"
            />
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setRejectingId(null)}
                className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-white text-xs"
              >
                Annulla
              </button>
              <button
                onClick={() => handleResolve(rejectingId, "REJECTED", rejectNote)}
                className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-500 text-white text-xs font-medium"
              >
                Conferma Rifiuto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
