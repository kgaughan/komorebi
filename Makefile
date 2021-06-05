develop: db.sqlite
	poetry update

run: develop
	KOMOREBI_SETTINGS=$(CURDIR)/dev/dev.cfg poetry run python -m komorebi --dev

build:
	find . -name \*.orig -delete
	poetry build --format wheel

clean:
	rm -rf db.sqlite

db.sqlite:
	sqlite3 db.sqlite < schema/komorebi.sql
	sqlite3 db.sqlite < schema/seed.sql

tidy:
	poetry run black komorebi
	poetry run isort komorebi

lint: 
	poetry run black --check komorebi
	poetry run isort --check komorebi
	@# This ignore if required by something black does with ':'
	poetry run flake8 --max-line-length=105 --ignore=E203 --per-file-ignores="komorebi/oembed.py:N802" komorebi
	poetry run pylint komorebi

test:
	poetry run python -m unittest discover -bf tests

.PHONY: clean develop run build tidy lint test
