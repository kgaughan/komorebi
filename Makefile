export KOMOREBI_SETTINGS=$(CURDIR)/dev/dev.cfg

develop: db.sqlite

run: develop
	hatch run flask --app komorebi --debug run

sri: develop
	hatch run flask --app komorebi sri

build:
	hatch build

clean:
	rm -rf db.sqlite

db.sqlite:
	sqlite3 db.sqlite < schema/komorebi.sql
	sqlite3 db.sqlite < schema/seed.sql

tidy:
	hatch run style:fmt

lint:
	hatch run style:check

test:
	hatch run test:unit

.PHONY: clean develop run build tidy lint test
