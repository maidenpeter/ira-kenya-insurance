#!/usr/bin/env bash
# Rebuild from ira-kenya-data (set IRA_DATA_DIR if it is not next to this repo).
set -e
python src/profitability/build.py
python src/profitability/build_page.py
python src/structure/build.py
python src/structure/build_page.py
