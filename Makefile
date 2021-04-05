develop: db.sqlite
	poetry update

run: develop
	KOMOREBI_SETTINGS=$(CURDIR)/dev/dev.cfg poetry run python -m komorebi

build:
	find . -name \*.orig -delete
	poetry build --format wheel

clean:
	rm -rf db.sqlite

db.sqlite:
	sqlite3 db.sqlite < schema/komorebi.sql
	sqlite3 db.sqlite < schema/seed.sql

.PHONY: clean develop run build
