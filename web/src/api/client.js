/**
 * Org3 Platform Unified API Client.
 * Dialoga con il backend FastAPI su /v1 (o BASE_URL configurato).
 */

const BASE_URL = import.meta.env.VITE_API_URL || "/v1";

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      let errorDetail = "Errore durante la richiesta al server";
      try {
        const errJson = await res.json();
        errorDetail = errJson.detail || errJson.message || errorDetail;
      } catch {
        errorDetail = await res.text();
      }
      throw new Error(errorDetail || `HTTP Error ${res.status}`);
    }
    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // --- Organizations & Workspaces ---
  organizations: {
    list: () => request("/organizations"),
    create: (data) => request("/organizations", { method: "POST", body: JSON.stringify(data) }),
    get: (orgId) => request(`/organizations/${orgId}`),
    update: (orgId, data) => request(`/organizations/${orgId}`, { method: "PATCH", body: JSON.stringify(data) }),
    listWorkspaces: (orgId) => request(`/organizations/${orgId}/workspaces`),
    createWorkspace: (orgId, data) => request(`/organizations/${orgId}/workspaces`, { method: "POST", body: JSON.stringify(data) }),
  },

  // --- Directory IAM & Members ---
  members: {
    list: (orgId, memberType) => {
      const q = memberType ? `?member_type=${memberType}` : "";
      return request(`/organizations/${orgId}/members${q}`);
    },
    create: (orgId, data) => request(`/organizations/${orgId}/members`, { method: "POST", body: JSON.stringify(data) }),
    get: (memberId) => request(`/members/${memberId}`),
    update: (memberId, data) => request(`/members/${memberId}`, { method: "PATCH", body: JSON.stringify(data) }),
  },

  // --- Delegation Policies & Evaluation Engine ---
  delegation: {
    list: (orgId, actorId) => {
      const q = actorId ? `?actor_id=${actorId}` : "";
      return request(`/organizations/${orgId}/policies${q}`);
    },
    create: (orgId, data) => request(`/organizations/${orgId}/policies`, { method: "POST", body: JSON.stringify(data) }),
    evaluateDryRun: (data) => request("/delegation/evaluate-dry-run", { method: "POST", body: JSON.stringify(data) }),
    evaluate: (data) => request("/delegation/evaluate", { method: "POST", body: JSON.stringify(data) }),
    authorize: (data, token) =>
      request("/delegation/authorize", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: JSON.stringify(data),
      }),
    revoke: (policyId) => request(`/delegation/policies/${policyId}`, { method: "DELETE" }),
  },

  // --- Approvals & HITL Hub ---
  approvals: {
    list: (orgId, status) => {
      const q = status ? `?status=${status}` : "";
      return request(`/organizations/${orgId}/approvals${q}`);
    },
    create: (data) => request("/approvals/request", { method: "POST", body: JSON.stringify(data) }),
    resolve: (approvalId, data) => request(`/approvals/${approvalId}/resolve`, { method: "POST", body: JSON.stringify(data) }),
  },

  // --- API Tokens & Connect ---
  tokens: {
    list: (orgId, memberId) => {
      const q = memberId ? `?member_id=${memberId}` : "";
      return request(`/organizations/${orgId}/tokens${q}`);
    },
    create: (data) => request("/tokens", { method: "POST", body: JSON.stringify(data) }),
    validate: (token) => request("/tokens/validate", { method: "POST", body: JSON.stringify({ token }) }),
    revoke: (tokenId) => request(`/tokens/${tokenId}`, { method: "DELETE" }),
  },

  // --- Multi-Cloud Storage & 10 Persistent Domains ---
  storage: {
    getCanonicalDomains: () => request("/storage/canonical-domains"),
    getCacheStats: () => request("/storage/cache/stats"),
    getStatus: (workspaceId) => request(`/workspaces/${workspaceId}/storage/status`),
    initDomains: (workspaceId) => request(`/workspaces/${workspaceId}/storage/init-domains`, { method: "POST" }),
    listItems: (workspaceId, domain, { subpath = "", recursive = false, forceRefresh = false } = {}) => {
      const q = new URLSearchParams();
      if (subpath) q.set("subpath", subpath);
      if (recursive) q.set("recursive", "true");
      if (forceRefresh) q.set("force_refresh", "true");
      const qs = q.toString() ? `?${q.toString()}` : "";
      return request(`/workspaces/${workspaceId}/storage/domains/${domain}/items${qs}`);
    },
    uploadItem: (workspaceId, domain, data) =>
      request(`/workspaces/${workspaceId}/storage/domains/${domain}/upload`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    getFingerprint: (workspaceId, domain) => request(`/workspaces/${workspaceId}/storage/domains/${domain}/fingerprint`),
    readContent: (workspaceId, itemId) => request(`/workspaces/${workspaceId}/storage/items/${encodeURIComponent(itemId)}/content`),
    deleteItem: (workspaceId, itemId) => request(`/workspaces/${workspaceId}/storage/items/${encodeURIComponent(itemId)}`, { method: "DELETE" }),
    invalidateCache: (workspaceId, domain) => {
      const q = domain ? `?domain=${domain}` : "";
      return request(`/workspaces/${workspaceId}/storage/cache/invalidate${q}`, { method: "POST" });
    },
  },
};
