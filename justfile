app := "komorebi"

[private]
default:
	@just --list

# setup virtual environment
devel:
	@uv sync --frozen

# tidy everything with ruff
tidy:
	@uv run --frozen ruff check --fix

# run dev server
dev-server:
	@uv run --frozen flask --app {{app}} --debug run

# regenerate SRI hashes
sri:
	@uv run --frozen flask --app {{app}} sri

# run the test suite
tests:
	@uv run --frozen pytest
