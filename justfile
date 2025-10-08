app := "komorebi"

default:
	@just --list

# setup virtual environment
devel:
	@uv sync --frozen

# run dev server
dev-server:
	@uv run flask --app {{app}} --debug run

# regenerate SRI hashes
sri:
	@uv run flask --app {{app}} sri
