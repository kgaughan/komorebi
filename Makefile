develop: .venv db.sqlite

run: develop
	FLASK_ENV=development .venv/bin/python -m komorebi

clean:
	rm -rf db.sqlite .venv

.venv:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/flit install --symlink

db.sqlite:
	sqlite3 db.sqlite < schema/komorebi.sql
	sqlite3 db.sqlite < schema/seed.sql

.PHONY: clean develop run
