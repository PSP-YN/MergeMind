import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.app.core.config import settings
from backend.app.models.workflow import Workflow, WorkflowEvent
from backend.app.security import decrypt_secret, encrypt_secret


class Store:
    def __init__(self, database_path: str | None = None):
        self.path = database_path or settings.database_path
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialise(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS workflows (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, encrypted INTEGER NOT NULL DEFAULT 0)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS switch_agents (role TEXT PRIMARY KEY, name TEXT NOT NULL, agent_id TEXT NOT NULL, secret TEXT NOT NULL)"
            )

    def save_workflow(self, workflow: Workflow) -> None:
        payload = workflow.model_dump_json()
        with self._connect() as db:
            db.execute(
                "INSERT INTO workflows(id, created_at, payload) VALUES(?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (workflow.id, workflow.created_at.isoformat(), payload),
            )

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM workflows WHERE id=?", (workflow_id,)).fetchone()
        return Workflow.model_validate_json(row["payload"]) if row else None

    def list_workflows(self, limit: int = 100) -> list[Workflow]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM workflows ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Workflow.model_validate_json(row["payload"]) for row in rows]

    def add_event(self, workflow_id: str, event: WorkflowEvent) -> Workflow:
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            raise KeyError(workflow_id)
        workflow.events.append(event)
        self.save_workflow(workflow)
        return workflow

    def set_setting(self, key: str, value: str, *, secret: bool = False) -> None:
        stored = encrypt_secret(value) if secret else value
        with self._connect() as db:
            db.execute(
                "INSERT INTO settings(key, value, encrypted) VALUES(?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, encrypted=excluded.encrypted",
                (key, stored, int(secret)),
            )

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT value, encrypted FROM settings WHERE key=?", (key,)).fetchone()
        if not row:
            return default
        return decrypt_secret(row["value"]) if row["encrypted"] else row["value"]

    def save_switch_agent(self, role: str, name: str, agent_id: str, api_key: str) -> None:
        encrypted = encrypt_secret(api_key)
        with self._connect() as db:
            db.execute(
                "INSERT INTO switch_agents(role, name, agent_id, secret) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(role) DO UPDATE SET name=excluded.name, agent_id=excluded.agent_id, secret=excluded.secret",
                (role, name, agent_id, encrypted),
            )

    def get_switch_agents(self) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute("SELECT role, name, agent_id, secret FROM switch_agents ORDER BY role").fetchall()
        return [
            {"role": row["role"], "name": row["name"], "agent_id": row["agent_id"], "api_key": decrypt_secret(row["secret"])}
            for row in rows
        ]

    def get_switch_agent(self, role: str) -> dict[str, str] | None:
        return next((agent for agent in self.get_switch_agents() if agent["role"] == role), None)

    def delete_all(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM workflows")
            db.execute("DELETE FROM settings")
            db.execute("DELETE FROM switch_agents")


store = Store()
