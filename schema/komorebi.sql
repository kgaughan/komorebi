CREATE TABLE links (
	id     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	title  TEXT    NOT NULL,
	link   TEXT    NULL     UNIQUE,
	via    TEXT    NULL,
	time_c TEXT    NOT NULL DEFAULT (DATETIME('now')),
	time_m TEXT    NOT NULL DEFAULT (DATETIME('now')),
	note   TEXT    NOT NULL
);

CREATE INDEX links_created ON links (time_c);
CREATE INDEX links_modified ON links (time_m);

-- Configuration dictionary for various plugins, extensions, &c.
CREATE TABLE config (
	dict  TEXT NOT NULL,
	key   TEXT NOT NULL,
	value TEXT NOT NULL
);
