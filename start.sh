#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Opret eller aktiver .venv
if [ -d ".venv" ]; then
    log "Virtual environment fundet – aktiverer..."
    source .venv/bin/activate
else
    warn "Virtual environment ikke fundet – opretter ny..."
    python3 -m venv .venv
    source .venv/bin/activate
    log "Virtual environment oprettet."
fi

# 2. Opdater pip
pip install --upgrade pip > /dev/null 2>&1

# 3. Installer requirements.txt (hvis den findes)
if [ -f "requirements.txt" ]; then
    log "Installer pakker fra requirements.txt..."
    pip install -r requirements.txt > /dev/null 2>&1
else
    warn "Ingen requirements.txt – opret med 'pip freeze > requirements.txt'"
fi

# 4. Kør stocks.py
if [ -f "stocks.py" ]; then
    log "Kører stocks.py..."
    python3 stocks.py
else
    error "stocks.py blev ikke fundet!"
    exit 1
fi