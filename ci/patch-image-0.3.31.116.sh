#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
# Surgical overlay: current updater CLI is preserved; hardened Recovery stays versioned.
install -m 0644 "$REPO/src/ui-language-0.3.27.js" "$ROOT/usr/share/2pny/ui-language.js"
install -d -m 0755 "$ROOT/usr/local/libexec"
install -m 0755 "$REPO/src/2pny-update-manager-0.3.31.112.py" "$ROOT/usr/local/libexec/2pny-update-manager-0.3.31.112.py"
install -m 0755 "$REPO/src/2pny-update-entrypoint-0.3.31.112.py" "$ROOT/usr/local/libexec/2pny-update-entrypoint-0.3.31.112.py"
printf '%s\n' '0.3.31.116' > "$ROOT/etc/2pny/version"
python3 -m py_compile "$ROOT/usr/local/libexec/2pny-update-manager-0.3.31.112.py" "$ROOT/usr/local/libexec/2pny-update-entrypoint-0.3.31.112.py"
cmp -s "$ROOT/usr/share/2pny/ui-language.js" "$REPO/src/ui-language-0.3.27.js"
cmp -s "$ROOT/usr/local/libexec/2pny-update-manager-0.3.31.112.py" "$REPO/src/2pny-update-manager-0.3.31.112.py"
cmp -s "$ROOT/usr/local/libexec/2pny-update-entrypoint-0.3.31.112.py" "$REPO/src/2pny-update-entrypoint-0.3.31.112.py"
test -x "$ROOT/usr/local/sbin/2pny-update-manager"
echo PATCH_IMAGE_0331116_OK
