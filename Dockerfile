FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Change thses to the repo and path you want to serve
ENV GITHUB_REPO=marimo-team/marimo
ENV GITHUB_ROOT_DIR=examples/ui

COPY main.py .
COPY templates/ templates/


CMD ["uv", "run", "--no-project", "main.py"]