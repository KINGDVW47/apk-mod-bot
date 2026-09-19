#!/usr/bin/env bash
# =============================================================================
# install.sh — Enstalasyon konplè pou APK Mod Bot (Linux)
# =============================================================================
set -euo pipefail

APKTOOL_VERSION="2.10.0"

echo "=============================================="
echo " APK Mod Bot — Enstalasyon"
echo "=============================================="

echo "[1/6] Enstale pakè sistèm (apktool, zipalign, apksigner, aapt, Java, Python)..."
sudo apt-get update
sudo apt-get install -y \
    apktool \
    zipalign \
    apksigner \
    aapt \
    aapt2 \
    default-jdk \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    unzip

echo "[2/6] Verifye ekzekitab yo..."
for cmd in zipalign apksigner keytool java python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ✓ $cmd -> $(command -v "$cmd")"
    else
        echo "  ✗ $cmd PA JWENN!" >&2
        exit 1
    fi
done

echo "[3/6] Enstale apktool v$APKTOOL_VERSION (dènye vèsyon GitHub)..."
sudo curl -L -o /usr/local/bin/apktool.jar \
    "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar"
sudo bash -c 'cat > /usr/local/bin/apktool <<EOF
#!/usr/bin/env bash
java -jar /usr/local/bin/apktool.jar "\$@"
EOF'
sudo chmod +x /usr/local/bin/apktool

if command -v apktool >/dev/null 2>&1; then
    echo "  ✓ apktool -> $(command -v apktool)"
else
    echo "  ✗ apktool PA JWENN!" >&2
    exit 1
fi

echo "  Verifye aapt / aapt2..."
if command -v aapt >/dev/null 2>&1; then
    echo "  ✓ aapt -> $(command -v aapt)"
elif command -v aapt2 >/dev/null 2>&1; then
    echo "  ✓ aapt2 -> $(command -v aapt2) (aapt sèvi kòm alias)"
else
    echo "  ⚠ aapt/aapt2 PA JWENN — apktool ap debake resous yo lè sa nesesè." >&2
fi

echo "[4/6] Enstale depandans Python..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[5/6] Kreye keystore pou siyati (si absent)..."
mkdir -p keys
KEYSTORE="keys/release.keystore"
ALIAS="modbot"
PASS="android"
DNAME="CN=APK Mod Bot, OU=Modding, O=ModBot, L=Port-au-Prince, S=Ouest, C=HT"

if [ -f "$KEYSTORE" ]; then
    echo "  ✓ Keystore deja egziste: $KEYSTORE"
else
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
    echo "  ✓ Keystore kreye: $KEYSTORE (alias=$ALIAS, pass=$PASS)"
fi

mkdir -p work uploads state

echo ""
echo "[6/6] Tout zouti enstale ak verifye ✅"
echo ""
echo "=============================================="
echo " Enstalasyon konplè ✅"
echo ""
echo " Pwochen etap:"
echo "   1. Ranpli BOT_TOKEN nan config.py (jwenn li nan @BotFather)"
echo "   2. Lanse bot la:  python3 bot.py"
echo "=============================================="
