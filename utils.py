# -*- coding: utf-8 -*-
"""
utils.py — Fonksyon itilite jeneral: validasyon, netwayaj, siyati.
"""
import os
import re
import shutil
import subprocess

from config import (
    APKSIGNER,
    KEYSTORE_ALIAS,
    KEYSTORE_PASS,
    KEYSTORE_PATH,
)

EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match((phone or "").strip()))


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w.\-]+", "_", name)
    return name.strip("._") or "file"


def run_cmd(cmd, cwd=None, timeout=600):
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def sign_apk(apk_path: str, out_path: str) -> tuple:
    if not os.path.exists(KEYSTORE_PATH):
        return False, f"Keystore pa jwenn: {KEYSTORE_PATH}"

    cmd = [
        APKSIGNER, "sign",
        "--ks", KEYSTORE_PATH,
        "--ks-pass", f"pass:{KEYSTORE_PASS}",
        "--ks-key-alias", KEYSTORE_ALIAS,
        "--out", out_path,
        apk_path,
    ]
    code, _, err = run_cmd(cmd, timeout=600)
    if code == 0:
        return True, "Siyati reyisi ✅"
    return False, f"Siyati echwe: {err.strip()[-500:]}"


def verify_apk(apk_path: str) -> tuple:
    cmd = [
        APKSIGNER, "verify",
        "--verbose",
        "--print-certs",
        apk_path,
    ]
    code, out, _ = run_cmd(cmd, timeout=120)
    if code == 0:
        return True, "Verifye reyisi ✅"
    return False, f"Verifye echwe: {out.strip()[-300:]}"
