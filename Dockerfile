FROM python:3.13-slim

# Install fonts for Pillow image rendering + uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev, frozen lockfile)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the app
COPY . .

# Heroku sets PORT dynamically
CMD ["uv", "run", "main.py"]
