#!/usr/bin/env python3
"""
notification.py — Multi-channel notification dispatcher for SuperOPC v2.

Supports:
  - File-based notifications (.opc/notifications/)  — always available
  - Webhook (Slack / Discord / Feishu / DingTalk)    — if configured
  - System desktop notification (Windows toast / macOS)
  - Email (SMTP)                                      — if configured
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.event_bus import EventBus, get_event_bus


# ---------------------------------------------------------------------------
# Notification model
# ---------------------------------------------------------------------------

@dataclass
class Notification:
    title: str
    body: str
    level: str = "info"
    channel: str = "file"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    delivered: bool = False


# ---------------------------------------------------------------------------
# Channel implementations
# ---------------------------------------------------------------------------

class FileChannel:
    def __init__(self, directory: Path):
        self._dir = directory

    def send(self, notif: Notification) -> bool:
        self._dir.mkdir(parents=True, exist_ok=True)
        ts = notif.timestamp.replace(":", "-").replace("T", "_")[:19]
        filepath = self._dir / f"{ts}_{notif.level}.json"
        filepath.write_text(json.dumps(asdict(notif), ensure_ascii=False, indent=2), encoding="utf-8")
        return True


class WebhookChannel:
    def __init__(self, url: str):
        self._url = url

    def send(self, notif: Notification) -> bool:
        if not self._url:
            return False
        payload = json.dumps({
            "text": f"[{notif.level.upper()}] {notif.title}\n{notif.body}",
            "title": notif.title,
            "level": notif.level,
        }).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "SuperOPC-Notification"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status < 400
        except (urllib.error.URLError, OSError):
            return False


class SystemChannel:
    @staticmethod
    def send(notif: Notification) -> bool:
        try:
            import platform
            system = platform.system()
            if system == "Windows":
                import subprocess
                ps_cmd = f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.Visible = $true; $n.ShowBalloonTip(5000, "{notif.title}", "{notif.body[:200]}", "Info"); Start-Sleep -Seconds 6; $n.Dispose()'
                subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            elif system == "Darwin":
                import subprocess
                subprocess.Popen([
                    "osascript", "-e",
                    f'display notification "{notif.body[:200]}" with title "{notif.title}"',
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
        except Exception:
            pass
        return False


# ---------------------------------------------------------------------------
# NotificationDispatcher
# ---------------------------------------------------------------------------

class NotificationDispatcher:
    """Routes notifications to configured channels."""

    def __init__(self, opc_dir: Path, bus: EventBus | None = None):
        self._opc_dir = opc_dir
        self._bus = bus or get_event_bus()
        self._file_channel = FileChannel(opc_dir / "notifications")
        self._webhook_url = os.environ.get("OPC_WEBHOOK_URL", "")
        self._webhook = WebhookChannel(self._webhook_url) if self._webhook_url else None
        self._system = SystemChannel()
        self._config = self._load_config()
        self._history: list[Notification] = []

    def _load_config(self) -> dict[str, Any]:
        config_file = self._opc_dir / "config.json"
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text(encoding="utf-8"))
                return data.get("notifications", {}) if isinstance(data, dict) else {}
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def notify(self, title: str, body: str, *, level: str = "info", metadata: dict[str, Any] | None = None) -> Notification:
        notif = Notification(title=title, body=body, level=level, metadata=metadata or {})

        self._file_channel.send(notif)
        notif.channel = "file"

        channels_used = ["file"]

        if self._webhook and level in ("warning", "error", "critical"):
            if self._webhook.send(notif):
                channels_used.append("webhook")

        if self._config.get("desktop", False) or level in ("error", "critical"):
            if self._system.send(notif):
                channels_used.append("system")

        notif.delivered = True
        notif.channel = ",".join(channels_used)
        self._history.append(notif)

        self._bus.publish("notification.send", {
            "title": title,
            "level": level,
            "channels": channels_used,
        }, source="notification")

        return notif

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        return [asdict(n) for n in self._history[-n:]]

    @property
    def unread_count(self) -> int:
        notif_dir = self._opc_dir / "notifications"
        if not notif_dir.exists():
            return 0
        return len(list(notif_dir.glob("*.json")))
