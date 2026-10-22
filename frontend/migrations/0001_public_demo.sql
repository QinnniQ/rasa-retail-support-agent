CREATE TABLE IF NOT EXISTS demo_sessions (
  id TEXT PRIMARY KEY,
  issue TEXT,
  order_id TEXT,
  updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  issue TEXT NOT NULL,
  reason TEXT NOT NULL,
  order_id TEXT,
  summary TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  assignee TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_unix INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS demo_cases_session ON demo_cases(session_id, id DESC);
CREATE TABLE IF NOT EXISTS demo_limits (
  key TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
