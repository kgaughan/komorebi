app := "komorebi"
docker_repo := "ghcr.io/kgaughan/" + app

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

# build the docker image
docker:
	@rm -rf dist
	@uv build --wheel
	@docker buildx build -t {{docker_repo}}:$(git describe --tags --always) .
	@docker tag {{docker_repo}}:$(git describe --tags --always) {{docker_repo}}:latest
