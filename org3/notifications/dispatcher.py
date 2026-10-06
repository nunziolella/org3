"""Unified Notification Dispatcher for Org3 Platform.

Dispatches high-priority Human-in-the-Loop (HITL) Class C/D approval alerts
directly to Nunzio's Telegram bot / webhook with deep-links, preventing bot sprawl.
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("org3.notifications")


class NotificationDispatcher:
    """Dispatches approval alerts and system notifications across channels."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        org3_base_url: Optional[str] = None,
        cuprite_base_url: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
        self.webhook_url = webhook_url or os.environ.get("TELEGRAM_WEBHOOK_URL")
        self.org3_base_url = (org3_base_url or os.environ.get("ORG3_BASE_URL", "https://org3.godigix.com")).rstrip("/")
        self.cuprite_base_url = (cuprite_base_url or os.environ.get("CUPRITE_BASE_URL", "https://cuprite.godigix.com")).rstrip("/")

    def format_approval_message(
        self,
        approval_id: str,
        org_slug: str,
        org_name: str,
        title: str,
        description: str,
        risk_class: str,
        source_service: str,
        requested_by_name: Optional[str] = None,
        financial_value: Optional[float] = None,
    ) -> str:
        """Costruisce il messaggio markdown con deep-link per Telegram."""
        deep_link = f"{self.org3_base_url}/app/?org={urllib.parse.quote(org_slug)}#approvals"
        cuprite_link = f"{self.cuprite_base_url}/app/approvals"

        risk_emoji = "🔴" if risk_class.upper() == "D" else "⚠️"
        lines = [
            f"{risk_emoji} *ORG3 HITL APPROVAL REQUIRED* [Classe {risk_class.upper()}]",
            f"🏢 *Organizzazione:* {org_name} (`{org_slug}`)",
            f"📌 *Titolo:* {title}",
            f"📝 *Descrizione:* {description}",
            f"⚡ *Sorgente:* `{source_service}`",
        ]
        if requested_by_name:
            lines.append(f"👤 *Richiesto da:* {requested_by_name}")
        if financial_value is not None and financial_value > 0:
            lines.append(f"💰 *Importo Coinvolto:* €{financial_value:,.2f}")

        lines.extend([
            "",
            f"👉 [Approva su Org3 Web]({deep_link})",
            f"👉 [Visualizza in Cuprite]({cuprite_link})",
        ])
        return "\n".join(lines)

    def dispatch_approval_alert(
        self,
        approval_id: str,
        org_slug: str,
        org_name: str,
        title: str,
        description: str,
        risk_class: str,
        source_service: str,
        requested_by_name: Optional[str] = None,
        financial_value: Optional[float] = None,
        sync: bool = True,
    ) -> Dict[str, Any]:
        """Invia l'avviso di approvazione HITL multicanale."""
        message = self.format_approval_message(
            approval_id=approval_id,
            org_slug=org_slug,
            org_name=org_name,
            title=title,
            description=description,
            risk_class=risk_class,
            source_service=source_service,
            requested_by_name=requested_by_name,
            financial_value=financial_value,
        )

        deep_link = f"{self.org3_base_url}/app/?org={urllib.parse.quote(org_slug)}#approvals"
        result = {
            "approval_id": approval_id,
            "dispatched": False,
            "channels": [],
            "deep_link": deep_link,
            "message": message,
            "error": None,
        }

        # 1. Dispatch via Telegram Bot API diretta
        if self.bot_token and self.chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        result["dispatched"] = True
                        result["channels"].append("telegram_bot")
                    else:
                        logger.warning(f"Telegram API responded with {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Failed to dispatch Telegram message: {e}")
                result["error"] = str(e)

        # 2. Dispatch via Webhook se configurato
        if self.webhook_url:
            try:
                payload = {
                    "event": "org3.hitl_approval_requested",
                    "approval_id": approval_id,
                    "org_slug": org_slug,
                    "risk_class": risk_class,
                    "message": message,
                    "deep_link": deep_link,
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(self.webhook_url, json=payload)
                    if resp.status_code in (200, 201, 202):
                        result["dispatched"] = True
                        result["channels"].append("webhook")
            except Exception as e:
                logger.error(f"Failed to post to webhook {self.webhook_url}: {e}")

        # Se nessun canale esterno è attivo (es. ambiente locale o test), simula il successo
        if not self.bot_token and not self.webhook_url:
            result["dispatched"] = True
            result["channels"].append("simulated_local")

        return result


# Singleton instance
_dispatcher_instance: Optional[NotificationDispatcher] = None


def get_dispatcher() -> NotificationDispatcher:
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = NotificationDispatcher()
    return _dispatcher_instance
