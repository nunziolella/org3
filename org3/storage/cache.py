"""Org3 Storage Anti-Quota Caching Engine & Rate-Limit Shield.

Protegge le API cloud (in primis Google Drive v3, che impone limiti a 100 req/100s per utente)
e i bucket S3/R2 da overhead e rate-limiting (HTTP 429 Too Many Requests):
1. In-Memory TTL Cache (default: 300s = 5 minuti).
2. Rate-Limiting Monitor: traccia le chiamate nel rolling window di 100s.
3. Anti-Quota Shield: serve risposte cached anche in caso di picchi improvvisi.
4. Auto-Invalidation: su ogni operazione di scrittura (write/delete), la cache del dominio viene invalidata selettivamente.
5. Exponential Backoff & Jitter: gestore trasparente per retry su errori transienti o 429.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger("org3.storage.cache")

T = TypeVar("T")


@dataclass
class CacheEntry:
    data: Any
    created_at: float
    ttl_seconds: float
    fingerprint: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class StorageCacheEngine:
    """Motore di Caching e Shield Anti-Quota per connettori Storage Org3."""

    def __init__(
        self,
        default_ttl_seconds: float = 300.0,
        rate_limit_window_seconds: float = 100.0,
        rate_limit_threshold_per_window: int = 80,
    ):
        self.default_ttl_seconds = default_ttl_seconds
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.rate_limit_threshold_per_window = rate_limit_threshold_per_window

        # Cache storage: key -> CacheEntry
        self._entries: Dict[str, CacheEntry] = {}

        # Rolling window call timestamps per workspace
        self._call_timestamps: Dict[str, deque] = {}

        # Metriche
        self._hits: int = 0
        self._misses: int = 0
        self._anti_quota_saves: int = 0
        self._evictions: int = 0

    def _build_key(self, workspace_id: str, scope: str, identifier: str) -> str:
        return f"{workspace_id}::{scope}::{identifier}"

    def get(self, workspace_id: str, scope: str, identifier: str) -> Optional[Any]:
        """Recupera un elemento dalla cache se presente e valido."""
        key = self._build_key(workspace_id, scope, identifier)
        entry = self._entries.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Se scaduto, verifichiamo se il rate limit è vicino al tetto per estendere la grazia anti-quota
        if entry.is_expired:
            if self.is_rate_limit_stressed(workspace_id):
                # Anti-quota grace hit: prolunghiamo l'uso del dato in cache per evitare 429
                self._anti_quota_saves += 1
                logger.warning(
                    "Anti-quota shield activated for %s: serving stale cache to prevent 429",
                    key,
                )
                return entry.data

            del self._entries[key]
            self._evictions += 1
            self._misses += 1
            return None

        self._hits += 1
        return entry.data

    def set(
        self,
        workspace_id: str,
        scope: str,
        identifier: str,
        data: Any,
        ttl_seconds: Optional[float] = None,
        fingerprint: Optional[str] = None,
    ) -> None:
        """Salva un elemento nella cache con TTL definito."""
        key = self._build_key(workspace_id, scope, identifier)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._entries[key] = CacheEntry(
            data=data,
            created_at=time.time(),
            ttl_seconds=ttl,
            fingerprint=fingerprint,
        )

    def invalidate(self, workspace_id: str, scope: Optional[str] = None, identifier: Optional[str] = None) -> int:
        """Invalida voci di cache per workspace, scope (es. dominio) o identificatore esatto."""
        prefix = f"{workspace_id}::"
        if scope:
            prefix += f"{scope}::"
            if identifier:
                prefix += identifier

        keys_to_remove = [k for k in self._entries if k.startswith(prefix) or (identifier and k == prefix)]
        for k in keys_to_remove:
            del self._entries[k]
            self._evictions += 1

        return len(keys_to_remove)

    def record_external_call(self, workspace_id: str) -> None:
        """Registra una chiamata esterna verso l'API per monitorare il rate-limiting."""
        now = time.time()
        if workspace_id not in self._call_timestamps:
            self._call_timestamps[workspace_id] = deque()

        q = self._call_timestamps[workspace_id]
        q.append(now)

        # Ripulisci eventi più vecchi della finestra di rolling
        cutoff = now - self.rate_limit_window_seconds
        while q and q[0] < cutoff:
            q.popleft()

    def is_rate_limit_stressed(self, workspace_id: str) -> bool:
        """Determina se le chiamate nel rolling window superano la soglia di sicurezza."""
        if workspace_id not in self._call_timestamps:
            return False

        now = time.time()
        cutoff = now - self.rate_limit_window_seconds
        q = self._call_timestamps[workspace_id]
        while q and q[0] < cutoff:
            q.popleft()

        return len(q) >= self.rate_limit_threshold_per_window

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche operative dello shield."""
        total_requests = self._hits + self._misses
        hit_ratio = round((self._hits / total_requests * 100), 2) if total_requests > 0 else 0.0

        return {
            "active_entries": len(self._entries),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio_percent": hit_ratio,
            "anti_quota_saves": self._anti_quota_saves,
            "evictions": self._evictions,
            "default_ttl_seconds": self.default_ttl_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def execute_with_anti_quota_retry(
        self,
        workspace_id: str,
        operation_name: str,
        coro_func: Callable[[], Coroutine[Any, Any, T]],
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
    ) -> T:
        """Esegue una chiamata remota con exponential backoff e jitter su errore 429 o transiente."""
        for attempt in range(max_retries + 1):
            self.record_external_call(workspace_id)
            try:
                return await coro_func()
            except Exception as exc:
                is_rate_limit = (
                    "429" in str(exc)
                    or "Too Many Requests" in str(exc)
                    or "User Rate Limit Exceeded" in str(exc)
                    or getattr(exc, "status_code", None) == 429
                )

                if is_rate_limit and attempt < max_retries:
                    self._anti_quota_saves += 1
                    delay = (base_delay_seconds * (2 ** attempt)) + random.uniform(0.1, 0.5)
                    logger.warning(
                        "Quota limit hit during %s (attempt %d/%d). Backing off for %.2fs...",
                        operation_name,
                        attempt + 1,
                        max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                # Se non è rate-limit o tentativi esauriti, rilancia
                raise exc
