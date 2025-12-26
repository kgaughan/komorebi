FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.12

# Install the dependencies.
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --group waitress

# Note: you must have built the wheel first, and there can only be one.
# We have to do it this way because we've hatch configured to lean on the VCS
# for versioning, `uv sync --locked --no-dev` won't work for us here.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=dist,target=dist \
    uv pip install --no-deps dist/*.whl

# Remove some junk to shrink the image a bit.
RUN <<EOT
cd /python/cpython-*-linux-x86_64-gnu
rm -rf include
rm -rf lib/itcl*
rm -rf lib/pkgconfig
rm -rf lib/libtcl*
rm -rf lib/libtk*
rm -rf lib/python*/lib-dynload/_tkinter.cpython-*.so
rm -rf lib/python*/tkinter
rm -rf lib/python*/turtle*
rm -rf lib/tcl*
rm -rf lib/tk*
EOT

FROM gcr.io/distroless/cc:nonroot

# Copy the Python version
COPY --from=builder /python /python

WORKDIR /app
# Copy the application from the builder
COPY --from=builder /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV KOMOREBI_SETTINGS=/config/komorebi.cfg

VOLUME ["/config", "/cache"]

EXPOSE 8000/tcp

ENTRYPOINT ["/app/.venv/bin/python3"]
CMD ["-m", "waitress", "--asyncore-use-poll", "--listen=0.0.0.0:8000", "--call", "komorebi:create_wsgi_app"]
