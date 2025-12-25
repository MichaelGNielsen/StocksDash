# Brug en officiel Python runtime som base image
# Din uv.lock kræver python >= 3.12
FROM python:3.12-slim

# Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Sæt arbejdsmappen i containeren
WORKDIR /app

# Kopier projekt-filer (pyproject.toml og uv.lock)
COPY pyproject.toml uv.lock ./

# Installer afhængigheder fra lock-filen
RUN uv sync --frozen --no-install-project

# Kopier resten af kildekoden
COPY . .

# Kommandoen til at køre din applikation
CMD ["uv", "run", "main.py"]