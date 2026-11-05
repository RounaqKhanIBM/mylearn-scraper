#!/usr/bin/env bash
# Launcher for scrape_course.py.
#
#   ./run.sh setup                             install dependencies and browser (run once)
#   ./run.sh login   "<course url>"            sign in once (opens a browser)
#   ./run.sh preview "<course url>" [options]  list what would be saved (dry run)
#   ./run.sh scrape  "<course url>" [options]  download transcripts to ./output
#
# [options] are passed through to scrape_course.py, e.g. --only-module 2 --out ./other_dir
set -euo pipefail

cd "$(dirname "$0")"
VENV=".venv"

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-1}"
}

[ $# -ge 1 ] || usage
CMD="$1"
shift
case "$CMD" in
    -h|--help|help) usage 0 ;;
    setup) exec bash ./setup.sh ;;
    login|preview|scrape) ;;
    *) echo "Unknown command: $CMD" >&2; usage ;;
esac

[ $# -ge 1 ] || { echo "Missing course URL." >&2; usage; }
URL="$1"
shift

case "$URL" in
    https://mylearn.oracle.com/*) ;;
    *) echo "URL must start with https://mylearn.oracle.com/" >&2; exit 1 ;;
esac

if [ ! -f "$VENV/.deps_installed" ] || [ requirements.txt -nt "$VENV/.deps_installed" ]; then
    echo "The environment is not set up yet. Run: ./run.sh setup" >&2
    exit 1
fi

case "$CMD" in
    login)   exec "$VENV/bin/python" scrape_course.py --login "$URL" "$@" ;;
    preview) exec "$VENV/bin/python" scrape_course.py --dry-run "$URL" "$@" ;;
    scrape)  exec "$VENV/bin/python" scrape_course.py "$URL" "$@" ;;
esac
