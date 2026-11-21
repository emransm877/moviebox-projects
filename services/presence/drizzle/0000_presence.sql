CREATE TABLE active_browsers (
  browser_id TEXT PRIMARY KEY NOT NULL,
  expires_at INTEGER NOT NULL
);
--> statement-breakpoint
CREATE INDEX active_browsers_expiry ON active_browsers (expires_at);
