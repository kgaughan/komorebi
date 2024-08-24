FROM python:3 AS build-env

# We're going to be installing everything into a directory, so this isn't needed.
ENV PIP_ROOT_USER_ACTION=ignore

# Using a context isn't enough: we need to mount the current directory within the build image.
RUN --mount=type=bind,target=/tmp/komorebi,rw <<END
# The Rye lockfile installs the app in editable mode, so we need to get rid of it.
sed -i '/^-e /d' /tmp/komorebi/requirements.lock

mkdir -p /opt/komorebi
pip3 install --target=/opt/komorebi --prefix= -r /tmp/komorebi/requirements.lock
pip3 install --target=/opt/komorebi --prefix= --no-deps /tmp/komorebi
END

FROM gcr.io/distroless/python3:latest
COPY --from=build-env /opt/komorebi /opt/komorebi

# This way, the application and its dependencies are importable.
ENV PYTHONPATH=/opt/komorebi
ENV KOMOREBI_SETTINGS=/path/to/app/komorebi.cfg
EXPOSE 8000
CMD ["-m", "komorebi", "--host", "0.0.0.0", "--port", "8000"]
