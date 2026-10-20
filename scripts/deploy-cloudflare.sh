#!/bin/sh
# Deploy site/ to Cloudflare Pages from a local machine using wrangler.
set -e

cd "$(dirname "$0")/.."

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER="wrangler"
elif command -v npx >/dev/null 2>&1; then
  WRANGLER="npx --yes wrangler"
else
  echo "error: wrangler is not installed." >&2
  echo "Install it with: npm install -g wrangler" >&2
  exit 1
fi

echo "Building site..."
python3 scripts/build.py
test -f site/index.html

echo "Deploying to Cloudflare Pages..."
OUTPUT=$($WRANGLER pages deploy site --project-name=flank-ledger)
echo "$OUTPUT"

# Print the deployment URL if wrangler reported one.
URL=$(printf '%s\n' "$OUTPUT" | grep -Eo 'https://[^ ]+' | head -n 1 || true)
if [ -n "$URL" ]; then
  echo "Deployed: $URL"
fi
