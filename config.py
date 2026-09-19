# -*- coding: utf-8 -*-
"""
config.py — Konfigirasyon santral pou bot Telegram APK Modder.

Remak: Itilizatè a dwe ranpli BOT_TOKEN la ak TOKEN botan li a.
Li ka jwenn token sa a nan @BotFather sou Telegram.
"""
import os

# =============================================================================
# Token Telegram — OBLIGATWA
# =============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")

# =============================================================================
# Relye chenn ekzekitab kòmand yo
# =============================================================================
APKTOOL = "apktool"
ZIPALIGN = "zipalign"
APKSIGNER = "apksigner"
KEYTOOL = "keytool"

# =============================================================================
# Keystore pou siyati
# =============================================================================
KEYSTORE_PATH = os.environ.get("KEYSTORE_PATH", "keys/release.keystore")
KEYSTORE_ALIAS = os.environ.get("KEYSTORE_ALIAS", "modbot")
KEYSTORE_PASS = os.environ.get("KEYSTORE_PASS", "android")
KEYSTORE_DNAME = os.environ.get(
    "KEYSTORE_DNAME",
    "CN=APK Mod Bot, OU=Modding, O=ModBot, L=Port-au-Prince, S=Ouest, C=HT",
)

# =============================================================================
# Repèrtwar travay ak tanporè
# =============================================================================
WORK_DIR = os.environ.get("WORK_DIR", "work")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
STATE_DIR = os.environ.get("STATE_DIR", "state")

# Limit: Taks maksimòm APK antre a. Itilizatè a mande 300 MB.
# Remak: Telegram Bot API sèlman pèmèt download/upload fichye jiska ~50 MB
MAX_APK_SIZE = 300 * 1024 * 1024  # 300 MB
