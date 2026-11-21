CREATE TABLE usage_counts (
  day TEXT NOT NULL,
  route TEXT NOT NULL,
  source TEXT NOT NULL,
  content TEXT NOT NULL,
  event TEXT NOT NULL,
  platform TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, route, source, content, event, platform)
);
