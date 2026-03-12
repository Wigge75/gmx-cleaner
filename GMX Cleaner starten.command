#!/bin/bash
# GMX Cleaner — Starter
# Doppelklick startet das Script im Terminal

# In den Ordner wechseln, in dem diese Datei liegt
cd "$(dirname "$0")"

# python-dotenv installieren falls nötig
pip3 install python-dotenv --quiet 2>/dev/null

# Script starten
python3 gmx_cleaner.py

# Terminal offen lassen nach Beenden
echo ""
echo "Drücke Enter zum Schließen..."
read
