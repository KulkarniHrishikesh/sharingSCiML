#!/bin/bash
# Download the large data files listed in data_manifest.csv from Cloudflare R2 and verify SHA-256.
# Usage:  bash fetch_data.sh                 # all files
#         bash fetch_data.sh light           # only paths containing "light"
#         LIST=1 bash fetch_data.sh          # show what would be downloaded
# Needs rclone with an R2 remote (default name "r2"; see README section "Large data on Cloudflare R2").
# Override with R2_REMOTE=<remote> and R2_BUCKET=<bucket>.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REMOTE=${R2_REMOTE:-r2}; BUCKET=${R2_BUCKET:-sharingsciml-data}; FILTER=${1:-}
sha(){ if command -v sha256sum >/dev/null; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
command -v rclone >/dev/null || { echo "rclone not found (install: https://rclone.org/install/)"; exit 2; }
fail=0
while IFS=, read -r path key size hash desc; do
    [ -n "$FILTER" ] && [[ "$path" != *"$FILTER"* ]] && continue
    dest="$HERE/$path"
    if [ -n "${LIST:-}" ]; then printf '%-40s %8.1f MB  %s\n' "$path" "$(echo "$size/1048576" | bc -l)" "$desc"; continue; fi
    if [ -f "$dest" ] && [ "$(sha "$dest")" = "$hash" ]; then echo "ok (already present): $path"; continue; fi
    mkdir -p "$(dirname "$dest")"
    echo "downloading $path ($size bytes)"
    rclone copyto "$REMOTE:$BUCKET/$key" "$dest" --s3-chunk-size 64M --progress || { echo "FAILED download: $path"; fail=1; continue; }
    if [ "$(sha "$dest")" = "$hash" ]; then echo "verified: $path"; else echo "CHECKSUM MISMATCH: $path"; fail=1; fi
done < <(tail -n +2 "$HERE/data_manifest.csv")
exit $fail
