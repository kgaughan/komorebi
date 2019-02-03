develop: .venv db.sqlite

run: develop
	PYTHONPATH=src .venv/bin/python -m komorebi

clean:
	rm -rf db.sqlite .venv

.venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

db.sqlite:
	sqlite3 db.sqlite < schema/komorebi.sql

.PHONY: clean develop run
