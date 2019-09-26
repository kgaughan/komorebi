develop: .venv db.sqlite

run: develop
	FLASK_ENV=development .venv/bin/python -m komorebi

build: .venv
	find . -name \*.orig -delete
	.venv/bin/flit build --format wheel

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

.PHONY: clean develop run build
