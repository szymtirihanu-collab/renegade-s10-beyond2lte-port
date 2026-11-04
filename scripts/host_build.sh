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

# The upstream build instructions require a second overlay: its Samsung SoC
# ACPI sources live outside mu-silicium-overlay. DeviceBuild.py also lists
# Platforms/Samsung as a package path, so create that package directory even
# though this port currently has no Samsung ACPI platform tables there.
ACPI_OVERLAY="$WORK/beyond2lte-upstream/silicium-acpi-overlay"
test -d "$ACPI_OVERLAY/SoCs/Samsung"
mkdir -p "$WORK/Mu-Silicium/Silicium-ACPI/SoCs"
cp -a "$ACPI_OVERLAY/SoCs/." "$WORK/Mu-Silicium/Silicium-ACPI/SoCs/"
mkdir -p "$WORK/Mu-Silicium/Silicium-ACPI/Platforms/Samsung"

# Fail early with a useful message if the package search paths drift again.
test -d "$WORK/Mu-Silicium/Silicium-ACPI/SoCs/Samsung"
test -d "$WORK/Mu-Silicium/Silicium-ACPI/Platforms/Samsung"

# The pinned Mu-Silicium snapshot does not contain the legacy GpioLib or
# SpeedyLib implementations referenced by this platform include. The current
# Samsung GPIO and Speedy DXE drivers do not consume either class: GpioDxe
# consumes GpioBankLib, and SpeedyDxe uses IoLib. Remove only these stale,
# unused library mappings from the temporary workspace so Stuart's path
# validator does not fail before compilation. Keep the repository source intact.
PLATFORM_DSC_INC="$WORK/Mu-Silicium/Silicon/Samsung/S5E9820Pkg/S5E9820Pkg.dsc.inc"
test -f "$PLATFORM_DSC_INC"
python3 - "$PLATFORM_DSC_INC" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
for line in (
    "  GpioLib|S5E9820Pkg/Library/GpioLib/GpioLib.inf\n",
    "  SpeedyLib|S5E9820Pkg/Library/SpeedyLib/SpeedyLib.inf\n",
):
    if line not in text:
        raise SystemExit(f"Expected stale mapping not found in {path}: {line.strip()}")
    text = text.replace(line, "")
path.write_text(text)
print("Removed two unimplemented, unused legacy library mappings in temporary build tree.")
PY

# B2LGoster stopped displaying the memory-map fragment count (Parca), but
# the counter's declaration and updates remained. Clang's -Werror rejects
# that dead local. Remove only the now-unused counter in the temporary tree.
B2L_GOSTER="$WORK/Mu-Silicium/Platforms/Samsung/beyond2ltePkg/Applications/B2LGoster/B2LGoster.c"
test -f "$B2L_GOSTER"
python3 - "$B2L_GOSTER" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
replacements = (
    ("    UINT32                 Parca;\n", ""),
    ("    Parca  = 0;\n", ""),
    ("          Parca++;\n", ""),
)
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one occurrence of {old.strip()!r} in {path}, found {count}")
    text = text.replace(old, new, 1)
path.write_text(text)
print("Removed obsolete Parca counter from temporary B2LGoster source.")
PY

echo "== Installing host build dependencies =="
sudo apt-get update
sudo apt-get install -y \
  git mono-devel build-essential make lld uuid-dev nasm \
  gcc-aarch64-linux-gnu python3 python3-venv python3-pip \
  gettext locales gnupg ca-certificates clang llvm curl

cd "$WORK/Mu-Silicium"
python3 -m venv "$WORK/venv"
. "$WORK/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r pip-requirements.txt
export CLANGPDB_AARCH64_PREFIX=aarch64-linux-gnu-

echo "== Compiling beyond2lte RELEASE UEFI =="
python ./build_uefi.py -d beyond2lte -r RELEASE -c

FD="$WORK/Mu-Silicium/Build/beyond2ltePkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd"
IMAGE="$WORK/Mu-Silicium/Mu-beyond2lte.img"
test -s "$FD"
test -s "$IMAGE"

echo "== Host build succeeded =="
file "$FD" "$IMAGE"
sha256sum "$FD" "$IMAGE"
echo "The image is a temporary CI build output. It is not uploaded, published, or flashed."
