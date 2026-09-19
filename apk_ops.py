# -*- coding: utf-8 -*-
"""
apk_ops.py — Operasyon APK nivo siperyè: dekonpile, rekonstwi, aliyen, siyen.

Flow konplè:
  1. dekonpile (apktool d)
  2. aplike patch (nan patcher.py)
  3. rekonstwi (apktool b)
  4. zipalign
  5. apksigner
"""
import os
import shutil

from config import APKTOOL, ZIPALIGN
from utils import run_cmd, sign_apk, safe_remove


class ApkBuildError(Exception):
    """Erè siperyè pou operasyon konpilasyon APK."""


def decompile(apk_path: str, out_dir: str) -> str:
    apk_base = os.path.splitext(os.path.basename(apk_path))[0]
    project_dir = os.path.join(out_dir, apk_base)

    code, out, err = run_cmd([APKTOOL, "d", "-f", "-o", project_dir, apk_path],
                             timeout=900)

    if code != 0:
        raise ApkBuildError(
            f"Dekonpilasyon echwe (apktool d):\n{err.strip()[-800:]}"
        )

    if not os.path.exists(os.path.join(project_dir, "AndroidManifest.xml")):
        raise ApkBuildError("Dekonpilasyon pwodui pa gen AndroidManifest.xml")

    return project_dir


def rebuild(project_dir: str, out_apk: str) -> str:
    code, out, err = run_cmd([APKTOOL, "b", project_dir, "-o", out_apk],
                             timeout=900)
    if code != 0:
        raise ApkBuildError(
            f"Rekonstriksyon echwe (apktool b):\n{err.strip()[-800:]}"
        )
    if not os.path.exists(out_apk):
        raise ApkBuildError(
            f"apktool pa pwodui fichye esperans: {out_apk}"
        )
    return out_apk


def zipalign(in_apk: str, out_apk: str) -> str:
    code, _, err = run_cmd([ZIPALIGN, "-f", "4", in_apk, out_apk],
                           timeout=600)
    if code != 0:
        raise ApkBuildError(
            f"zipalign echwe: {err.strip()[-400:]}"
        )
    return out_apk


def full_build_pipeline(project_dir: str, work_root: str, apk_base: str):
    try:
        unsigned = os.path.join(work_root, apk_base + "_unsigned.apk")
        aligned = os.path.join(work_root, apk_base + "_aligned.apk")
        signed = os.path.join(work_root, apk_base + "_mod.apk")

        rebuild(project_dir, unsigned)
        zipalign(unsigned, aligned)

        ok, msg = sign_apk(aligned, signed)
        if not ok:
            return False, None, msg

        return True, signed, "Konpilasyon + siyati reyisi ✅"

    except ApkBuildError as e:
        return False, None, str(e)
