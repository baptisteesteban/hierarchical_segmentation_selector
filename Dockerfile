FROM ghcr.io/astral-sh/uv:python3.14-trixie

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . ./

CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:8000", "app:app"]