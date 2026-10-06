import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  ShieldCheck,
  Bot,
  Cpu,
  User,
  ShieldAlert,
  Search,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { api } from "../api/client";

export function DirectoryIAM({ currentOrg }) {
  const [members, setMembers] = useState([]);
  const [filterType, setFilterType] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Modal Nuovo Membro
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [memberType, setMemberType] = useState("HUMAN");
  const [role, setRole] = useState("OPERATOR");
  const [isMaster, setIsMaster] = useState(false);

  const loadMembers = async () => {
    if (!currentOrg?.id) return;
    setLoading(true);
    try {
      const typeParam = filterType === "ALL" ? null : filterType;
      const data = await api.members.list(currentOrg.id, typeParam);
      setMembers(data || []);
    } catch (err) {
      setError("Errore caricamento membri: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [currentOrg?.id, filterType]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!currentOrg?.id) return;

    setError(null);
    setSuccess(null);

    try {
      await api.members.create(currentOrg.id, {
        name,
        email,
        member_type: memberType,
        role,
        is_master: isMaster || email.trim().toLowerCase() === "01nunzio.lella@gmail.com",
      });

      setSuccess(`Membro ${name} aggiunto con successo alla Directory!`);
      setShowModal(false);
      setName("");
      setEmail("");
      setMemberType("HUMAN");
      setRole("OPERATOR");
      setIsMaster(false);
      loadMembers();
    } catch (err) {
      setError("Errore creazione membro: " + err.message);
    }
  };

  const filteredMembers = members.filter((m) => {
    const q = searchQuery.toLowerCase();
    return m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q) || m.role.toLowerCase().includes(q);
  });

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Users className="w-7 h-7 text-accent-orange" />
            <span>Directory Unificata IAM (Umani, Agenti AI & Worker)</span>
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Gestione delle identità, ruoli organizzativi Org3 e assegnazione del privilegio sovrano God Mode.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-orange hover:bg-accent-orangeHover text-white font-medium text-sm transition shadow-lg shadow-accent-orange/20"
        >
          <UserPlus className="w-4 h-4" />
          <span>Nuovo Attore / Membro</span>
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

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4 bg-dark-900 p-4 rounded-xl border border-dark-700">
        <div className="flex items-center gap-2">
          {["ALL", "HUMAN", "AI_SYSTEM", "WORKER_SERVICE"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono uppercase transition ${
                filterType === type
                  ? "bg-accent-orange text-white shadow-sm"
                  : "bg-dark-800 text-neutral-400 hover:text-white hover:bg-dark-750"
              }`}
            >
              {type === "ALL" && "Tutti"}
              {type === "HUMAN" && "Umani"}
              {type === "AI_SYSTEM" && "Agenti AI"}
              {type === "WORKER_SERVICE" && "Worker"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cerca per nome o email..."
              className="bg-dark-800 border border-dark-700 rounded-md pl-9 pr-4 py-1.5 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-accent-orange w-64"
            />
          </div>

          <button
            onClick={loadMembers}
            className="p-2 rounded-md bg-dark-800 border border-dark-700 text-neutral-400 hover:text-white transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Members Grid / Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMembers.map((member) => (
          <div
            key={member.id}
            className={`p-5 rounded-xl border transition flex flex-col justify-between ${
              member.is_master
                ? "bg-gradient-to-b from-dark-900 to-dark-850 border-accent-orange/40 shadow-lg shadow-accent-orange/5"
                : "bg-dark-900 border-dark-700 hover:border-dark-600"
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm ${
                      member.member_type === "HUMAN"
                        ? "bg-blue-950/60 text-blue-400 border border-blue-800"
                        : member.member_type === "AI_SYSTEM"
                        ? "bg-purple-950/60 text-purple-400 border border-purple-800"
                        : "bg-amber-950/60 text-amber-400 border border-amber-800"
                    }`}
                  >
                    {member.member_type === "HUMAN" && <User className="w-5 h-5" />}
                    {member.member_type === "AI_SYSTEM" && <Bot className="w-5 h-5" />}
                    {member.member_type === "WORKER_SERVICE" && <Cpu className="w-5 h-5" />}
                  </div>

                  <div>
                    <div className="font-bold text-white text-sm flex items-center gap-2">
                      <span>{member.name}</span>
                    </div>
                    <div className="text-xs text-neutral-400 font-mono">{member.email}</div>
                  </div>
                </div>
              </div>

              {/* God Mode Indicator */}
              {member.is_master && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent-orange/15 border border-accent-orange/30 text-accent-orange text-xs font-mono font-bold">
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  <span>MASTER ASSOLUTO (GOD MODE)</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-dark-850 p-2.5 rounded-lg border border-dark-800 text-neutral-400">
                <div>
                  <span className="text-neutral-500 block uppercase">Ruolo:</span>
                  <span className="text-neutral-200 font-semibold">{member.role}</span>
                </div>
                <div>
                  <span className="text-neutral-500 block uppercase">Tipo:</span>
                  <span className="text-neutral-200">{member.member_type}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-dark-800 flex items-center justify-between text-xs text-neutral-500">
              <span>Stato: {member.is_active ? "Attivo" : "Disattivato"}</span>
              <span className="font-mono text-[10px]">{member.id.substring(0, 8)}...</span>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Nuovo Membro */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-6 max-w-lg w-full space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Nuovo Attore / Membro Org3</h3>
              <button onClick={() => setShowModal(false)} className="text-neutral-500 hover:text-neutral-300 text-sm">
                Chiudi
              </button>
            </div>

            <form onSubmit={handleAddMember} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Nome o Identificativo</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="es. Nunzio Lella, PAI Researcher, clickup-worker"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Email / Identificativo Unico</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="es. collaboratore@azienda.it o worker@internal.bot"
                  className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Tipo Attore</label>
                  <select
                    value={memberType}
                    onChange={(e) => setMemberType(e.target.value)}
                    className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  >
                    <option value="HUMAN">HUMAN (Umano)</option>
                    <option value="AI_SYSTEM">AI_SYSTEM (Agente Cognitivo)</option>
                    <option value="WORKER_SERVICE">WORKER_SERVICE (Operatore)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono uppercase text-neutral-400 mb-1">Ruolo Org3</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full bg-dark-800 border border-dark-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-accent-orange"
                  >
                    <option value="OPERATOR">OPERATOR</option>
                    <option value="TECH_LEAD">TECH_LEAD</option>
                    <option value="CEO">CEO</option>
                    <option value="VP">VP</option>
                    <option value="VIEWER">VIEWER</option>
                    <option value="FOUNDER_GODMODE">FOUNDER_GODMODE</option>
                  </select>
                </div>
              </div>

              <div className="p-3 bg-dark-850 rounded-lg border border-dark-800 flex items-center gap-3">
                <input
                  type="checkbox"
                  id="masterToggle"
                  checked={isMaster || email.trim().toLowerCase() === "01nunzio.lella@gmail.com"}
                  onChange={(e) => setIsMaster(e.target.checked)}
                  className="rounded bg-dark-800 border-dark-700 text-accent-orange focus:ring-0"
                />
                <label htmlFor="masterToggle" className="text-xs text-neutral-300">
                  <span className="font-bold text-accent-orange">God Mode (Master Assoluto)</span>: bypass totale di ogni gate di rischio e veto sovrano.
                </label>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-md bg-dark-800 text-neutral-400 hover:text-neutral-200 text-sm"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-md bg-accent-orange hover:bg-accent-orangeHover text-white text-sm font-medium"
                >
                  Aggiungi Membro
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
