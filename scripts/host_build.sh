#!/usr/bin/env bash
# Reproducible host-only candidate build. No phone access, flashing, or packaging.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="$ROOT/UPSTREAM.lock.json"
WORK="${RUNNER_TEMP:-/tmp}/beyond2lte-host-build"
UPSTREAM_URL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["uefi_upstream"]["repository"])' "$LOCK")"
UPSTREAM_COMMIT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["uefi_upstream"]["commit"])' "$LOCK")"
MU_URL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["mu_silicium_reference_snapshot"]["repository"])' "$LOCK")"
MU_COMMIT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["mu_silicium_reference_snapshot"]["commit"])' "$LOCK")"

rm -rf "$WORK"
mkdir -p "$WORK"

echo "== Fetching beyond2lte overlay at $UPSTREAM_COMMIT =="
git clone --filter=blob:none --no-checkout "$UPSTREAM_URL" "$WORK/beyond2lte-upstream"
git -C "$WORK/beyond2lte-upstream" checkout --detach "$UPSTREAM_COMMIT"
test -d "$WORK/beyond2lte-upstream/mu-silicium-overlay"

echo "== Fetching Mu-Silicium at $MU_COMMIT =="
git clone --filter=blob:none --no-checkout "$MU_URL" "$WORK/Mu-Silicium"
git -C "$WORK/Mu-Silicium" checkout --detach "$MU_COMMIT"
git -C "$WORK/Mu-Silicium" submodule sync --recursive
git -C "$WORK/Mu-Silicium" submodule update --init --recursive

if git -C "$WORK/Mu-Silicium" submodule status --recursive | grep -E '^[+-U]'; then
  echo "ERROR: a recursive submodule is not at the commit recorded by its parent tree."
  exit 1
fi

echo "== Applying device overlay in the temporary build workspace =="
cp -a "$WORK/beyond2lte-upstream/mu-silicium-overlay/." "$WORK/Mu-Silicium/"

echo "== Installing the pinned project's host build dependencies =="
cd "$WORK/Mu-Silicium"
CI_BUILD=false bash ./setup_env.sh -p apt

echo "== Compiling beyond2lte RELEASE UEFI =="
python3 ./build_uefi.py -d beyond2lte -r RELEASE -c

FD="$WORK/Mu-Silicium/Build/beyond2ltePkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd"
IMAGE="$WORK/Mu-Silicium/Mu-beyond2lte.img"
test -s "$FD"
test -s "$IMAGE"

echo "== Host build succeeded =="
file "$FD" "$IMAGE"
sha256sum "$FD" "$IMAGE"
echo "The image is a temporary CI build output. It is not uploaded, published, or flashed."
