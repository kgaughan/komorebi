-- Some data to seed the tables with.

INSERT INTO links (
	title,
	link,
	via,
	time_c,
	time_m,
	note
) VALUES (
	'This is a title',
	'https://example.com/',
	NULL,
	DATETIME('now'),
	DATETIME('now'),
	'The accompanying note.'
), (
	'This is another title',
	NULL,
	'https://example.com/',
	DATETIME('now'),
	DATETIME('now'),
	'And this is another accompanying note.'
), (
	'This is another title',
	NULL,
	NULL,
	DATETIME('now'),
	DATETIME('now'),
	'And this is another accompanying note.'
);
