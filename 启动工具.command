#!/bin/zsh
set -e
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import PySide6, search_submitter' 2>/dev/null; then
  .venv/bin/python -m pip install --upgrade pip setuptools
  .venv/bin/pip install -r requirements.txt
fi
if [[ "$(uname)" == "Darwin" ]]; then
  find .venv/lib/python*/site-packages/PySide6/Qt/plugins -type f -exec chflags nohidden {} + 2>/dev/null || true
fi
exec .venv/bin/python run.py
