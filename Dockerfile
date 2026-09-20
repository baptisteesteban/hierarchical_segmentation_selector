FROM ghcr.io/astral-sh/uv:python3.14-trixie

WORKDIR /app
COPY . ./

RUN uv sync
ENTRYPOINT ["uv", "run", "app.py"]