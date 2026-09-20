FROM ghcr.io/astral-sh/uv:python3.14-trixie

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . ./
ENTRYPOINT ["uv", "run", "app.py"]