#!/usr/bin/env bash
# Rebuild from ira-kenya-data (set IRA_DATA_DIR if it is not next to this repo). The reinsurance module
# also reads the Cedant Scorecard from ira-kenya-reinsurance (IRA_REINSURANCE_DIR).
set -e
python src/profitability/build.py
python src/profitability/build_page.py
python src/structure/build.py
python src/structure/build_page.py
python src/reinsurance/build.py
python src/reinsurance/build_page.py
python src/claims/build.py
python src/claims/build_page.py
