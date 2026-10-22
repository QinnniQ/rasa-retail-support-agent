import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import CaseCreate, CaseUpdate


def redact(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[e-mail verwijderd]", text)
    return re.sub(r"\b(?:\+31|0)[\d\s-]{8,14}\b", "[telefoon verwijderd]", text)


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, issue TEXT, order_id TEXT, history TEXT NOT NULL DEFAULT '[]')")
            db.execute("CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, issue TEXT NOT NULL, reason TEXT NOT NULL, order_id TEXT, summary TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', assignee TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def session(self, session_id: str) -> dict:
        with self.connection() as db:
            row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else {"id": session_id, "issue": None, "order_id": None, "history": "[]"}

    def save_session(self, session: dict, message: str, answer: str):
        history = json.loads(session["history"])
        history.append({"user": redact(message[:300]), "assistant": redact(answer[:500])})
        with self.connection() as db:
            db.execute("INSERT INTO sessions(id,issue,order_id,history) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET issue=excluded.issue,order_id=excluded.order_id,history=excluded.history", (session["id"], session["issue"], session["order_id"], json.dumps(history[-20:])))

    def create_case(self, case: CaseCreate) -> dict:
        with self.connection() as db:
            cur = db.execute("INSERT INTO cases(session_id,issue,reason,order_id,summary) VALUES(?,?,?,?,?)", (case.session_id, case.issue, redact(case.reason), case.order_id, redact(case.summary)))
            row = db.execute("SELECT * FROM cases WHERE id=?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def cases(self, status: str | None = None) -> list[dict]:
        with self.connection() as db:
            rows = db.execute("SELECT * FROM cases WHERE status=? ORDER BY id DESC" if status else "SELECT * FROM cases ORDER BY id DESC", (status,) if status else ()).fetchall()
        return [dict(row) for row in rows]

    def update_case(self, case_id: int, update: CaseUpdate) -> dict | None:
        with self.connection() as db:
            row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
            if not row:
                return None
            values = update.model_dump(exclude_unset=True)
            if values:
                db.execute("UPDATE cases SET status=?, assignee=? WHERE id=?", (values.get("status", row["status"]), values.get("assignee", row["assignee"]), case_id))
            return dict(db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone())
