#!/usr/bin/env bash
# =============================================================================
# start.sh — Script demaraj pou APK Mod Bot (pou Railway / Docker)
# =============================================================================
set -euo pipefail

echo "=============================================="
echo " APK Mod Bot — Demaraj"
echo "=============================================="

if [ -z "${BOT_TOKEN:-}" ]; then
    echo "❌ ERÈ: BOT_TOKEN pa defini!" >&2
    echo "   Mete l nan Railway (Variables) oswa: export BOT_TOKEN=..." >&2
    exit 1
fi

echo "[1/3] Verifye zouti yo..."
for cmd in apktool zipalign apksigner keytool java python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ✓ $cmd"
    else
        echo "  ✗ $cmd PA JWENN!" >&2
        exit 1
    fi
done

echo "[2/3] Kreye keystore siyati (si absent)..."
mkdir -p keys
KEYSTORE="keys/release.keystore"
ALIAS="${KEYSTORE_ALIAS:-modbot}"
PASS="${KEYSTORE_PASS:-android}"
DNAME="CN=APK Mod Bot, OU=Modding, O=ModBot, L=Port-au-Prince, S=Ouest, C=HT"

if [ ! -f "$KEYSTORE" ]; then
    keytool -genkeypair \
        -v \
        -keystore "$KEYSTORE" \
        -alias "$ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$PASS" \
        -keypass "$PASS" \
        -dname "$DNAME"
    echo "  ✓ Keystore kreye: $KEYSTORE"
else
    echo "  ✓ Keystore deja egziste: $KEYSTORE"
fi

echo "[3/3] Lanse bot la (long polling)..."
echo "=============================================="
exec python3 bot.py
