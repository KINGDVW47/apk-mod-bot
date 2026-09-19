# -*- coding: utf-8 -*-
"""
patcher.py — Modil pou tout operasyon "patching" sou yon APK dekonpile.

Li kontni fonksyon ki modifye yon pwojè dekonpile (smali + res),
epi rapòte konbyen fichye oswa okirans yo chanje.
"""
import os
import re
import shutil


def change_app_name(decompiled_dir: str, new_name: str, strings_file: str) -> dict:
    report = {"label_changed": False, "detail": ""}
    manifest_path = _find_manifest(decompiled_dir)
    strings_path = strings_file or _find_strings(decompiled_dir)

    if not manifest_path:
        report["detail"] = "AndroidManifest.xml pa jwenn"
        return report

    manifest = open(manifest_path, encoding="utf-8").read()

    m = re.search(r'android:label="([^"]+)"', manifest)
    ref_changed = False

    if m:
        label_value = m.group(1)
        if label_value.startswith("@string/"):
            key = label_value[len("@string/"):]
            if strings_path and os.path.exists(strings_path):
                ref_changed = _replace_string_value(
                    strings_path, key, new_name
                )
            if not ref_changed:
                manifest = manifest.replace(
                    f'android:label="{label_value}"',
                    f'android:label="{new_name}"',
                )
        else:
            manifest = manifest.replace(
                f'android:label="{label_value}"',
                f'android:label="{new_name}"',
            )
            report["label_changed"] = True
    else:
        manifest = _add_application_attribute(manifest, "android:label", new_name)

    open(manifest_path, "w", encoding="utf-8").write(manifest)

    if ref_changed:
        report["label_changed"] = True
        report["detail"] = f"Referans @string modifye nan strings.xml: {new_name}"
    elif report["label_changed"]:
        report["detail"] = f"Label literal modifye nan manifest: {new_name}"

    return report


def inject_custom_strings(strings_file: str, values: dict) -> dict:
    report = {"injected": [], "detail": ""}

    if not strings_file or not os.path.exists(strings_file):
        report["detail"] = "strings.xml pa jwenn pou enjeksyon"
        return report

    content = open(strings_file, encoding="utf-8").read()

    if "</resources>" not in content:
        report["detail"] = "strings.xml kòwonpi (pa gen </resources>)"
        return report

    injected = []
    for key, val in values.items():
        if f'name="{key}"' in content:
            continue
        line = f'    <string name="{key}">{_xml_escape(val)}</string>\n'
        injected.append(line)
        report["injected"].append(key)

    if injected:
        content = content.replace("</resources>", "".join(injected) + "</resources>")
        open(strings_file, "w", encoding="utf-8").write(content)
        report["detail"] = f"{len(injected)} resous enjekte: {', '.join(injected)}"
    else:
        report["detail"] = "Pa gen nouvo resous (yo te deja egziste)"

    return report


def inject_toast(decompiled_dir: str, toast_msg: str) -> dict:
    report = {"toast_injected": False, "detail": ""}

    launcher_class = _find_launcher_class(decompiled_dir)
    if not launcher_class:
        report["detail"] = "Aktivite launcher pa detèmine"
        return report

    smali_path = _class_to_smali_path(decompiled_dir, launcher_class)
    if not smali_path or not os.path.exists(smali_path):
        report["detail"] = f"Fichye smali pa jwenn pou {launcher_class}"
        return report

    content = open(smali_path, encoding="utf-8").read()

    if ".method" not in content:
        report["detail"] = "Pa gen metòd nan klas launcher a"
        return report

    m = re.search(
        r"\.method[^\n]*\bonCreate\b\(Landroid/os/Bundle;\)V\b",
        content,
    )
    if not m:
        report["detail"] = "onCreate(Bundle)V pa jwenn"
        return report

    method_start = m.start()

    next_method = content.find(".method", method_start + 1)
    method_end = next_method if next_method != -1 else len(content)
    method_body = content[method_start:method_end]

    super_idx = method_body.find("invoke-super")
    if super_idx == -1:
        report["detail"] = "invoke-super pa jwenn nan onCreate"
        return report

    line_end = method_body.find("\n", super_idx)
    if line_end == -1:
        line_end = len(method_body)
    insert_pos = method_start + line_end + 1

    toast_smali = (
        "\n    # --- Enjeksyon Toast (apk-mod-bot) ---\n"
        "    const-string v0, " + _str_to_smali_format(toast_msg) + "\n"
        "    const/4 v1, 0x1\n"
        "    invoke-static {v0, v1}, Landroid/widget/Toast;->makeText"
        "(Landroid/content/Context;Ljava/lang/CharSequence;I)"
        "Landroid/widget/Toast;\n"
        "    move-result-object v0\n"
        "    invoke-virtual {v0}, Landroid/widget/Toast;->show()V\n"
        "    # --- Fen enjeksyon ---\n"
    )

    content = content[:insert_pos] + toast_smali + content[insert_pos:]
    open(smali_path, "w", encoding="utf-8").write(content)
    report["toast_injected"] = True
    report["detail"] = f"Toast enjekte nan {launcher_class} -> onCreate"

    return report


def remove_lvl(decompiled_dir: str) -> dict:
    return _remove_patterns_in_smali(
        decompiled_dir,
        "LVL",
        patterns=[
            r"com/android/vending/licensing",
            r"LicenseChecker",
            r"ILicenseChecker",
            r"checkAccess",
        ],
        replacements=[
            (r"Lcom/android/vending/licensing/LicenseChecker;",
             "Ljava/lang/Object;"),
        ],
    )


def remove_ads(decompiled_dir: str) -> dict:
    return _remove_patterns_in_smali(
        decompiled_dir,
        "ADS",
        patterns=[
            r"com/google/android/gms/ads",
            r"com/facebook/ads",
            r"com/unity3d/ads",
            r"com/mopub",
            r"com/applovin",
            r"com/startapp",
            r"com/ironsource",
        ],
        replacements=[
            (r"Lcom/google/android/gms/ads/.*?;", "Ljava/lang/Object;"),
            (r"Lcom/facebook/ads/.*?;", "Ljava/lang/Object;"),
        ],
    )


def remove_root_detection(decompiled_dir: str) -> dict:
    return _remove_patterns_in_smali(
        decompiled_dir,
        "ROOT",
        patterns=[
            r"com/scottyab/rootbeer",
            r"com/google/android/gms/safetynet",
            r"com/topjohnwu/superuser",
            r"/system/bin/su",
            r"/sbin/su",
            r"which su",
        ],
        replacements=[],
    )


def remove_signature_check(decompiled_dir: str) -> dict:
    return _remove_patterns_in_smali(
        decompiled_dir,
        "SIGNATURE",
        patterns=[
            r"getPackageInfo",
            r"GET_SIGNATURES",
            r"GET_SIGNING_CERTIFICATES",
            r"signatures",
            r"signingInfo",
        ],
        replacements=[],
    )


def patch_plan_credit_token(decompiled_dir: str) -> dict:
    report = {
        "label": "PLAN/CREDIT/TOKEN",
        "files_scanned": 0,
        "methods_patched": 0,
        "detail": "",
    }

    boolean_methods = re.compile(
        r"(?:\\.method[^\n]*?\s)(isPremium|isVip|isVipMember|isPro|isSubscribed|"
        r"hasSubscription|hasActiveSubscription|hasPremium|isPremiumUser|"
        r"isTokenValid|hasValidToken|isTokenActive|isUnlocked|isActivated|"
        r"isPurchased|hasPurchased|isPaid|verify|isValid)\(\)Z",
        re.IGNORECASE,
    )

    credit_methods = re.compile(
        r"(?:\\.method[^\n]*?\s)(getCredits|getCoins|getBalance|getTokens|"
        r"getPoints|getGems|getDiamonds|getGold|getCash|getMoney)\(\)(I|J)",
        re.IGNORECASE,
    )

    for root, dirs, files in os.walk(decompiled_dir):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            path = os.path.join(root, fname)
            try:
                content = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            report["files_scanned"] += 1

            new_content = content
            new_content = _patch_boolean_methods(new_content, boolean_methods)
            new_content = _patch_credit_methods(new_content, credit_methods)

            if new_content != content:
                open(path, "w", encoding="utf-8").write(new_content)
                delta = _count_new_markers(content, new_content)
                report["methods_patched"] += delta

    if report["methods_patched"] == 0:
        report["detail"] = "PLAN/CREDIT/TOKEN: okenn metòd rekonèt jwenn"
    else:
        report["detail"] = (
            f"PLAN/CREDIT/TOKEN: {report['methods_patched']} metòd patch "
            f"(plan/premium + kredi + token)"
        )
    return report


def _find_manifest(decompiled_dir: str):
    p = os.path.join(decompiled_dir, "AndroidManifest.xml")
    return p if os.path.exists(p) else None


def _find_strings(decompiled_dir: str):
    p = os.path.join(decompiled_dir, "res", "values", "strings.xml")
    return p if os.path.exists(p) else None


def _replace_string_value(strings_file: str, key: str, new_value: str) -> bool:
    content = open(strings_file, encoding="utf-8").read()
    pattern = re.compile(
        r'(<string name="' + re.escape(key) + r'"[^>]*>)(.*?)(</string>)',
        re.DOTALL,
    )
    new_content, n = pattern.subn(
        lambda mm: mm.group(1) + _xml_escape(new_value) + mm.group(3),
        content,
        count=1,
    )
    if n == 0:
        return False
    open(strings_file, "w", encoding="utf-8").write(new_content)
    return True


def _add_application_attribute(manifest: str, attr: str, value: str) -> str:
    tag_open = re.search(r"<application\b", manifest)
    if not tag_open:
        return manifest
    insert = f' {attr}="{_xml_escape(value)}"'
    return manifest[:tag_open.end()] + insert + manifest[tag_open.end():]


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _find_launcher_class(decompiled_dir: str):
    manifest_path = _find_manifest(decompiled_dir)
    if not manifest_path:
        return None
    content = open(manifest_path, encoding="utf-8").read()

    activity_blocks = re.findall(
        r"<activity\b[^>]*>(.*?)</activity>",
        content,
        re.DOTALL,
    )
    for block in activity_blocks:
        if "android.intent.action.MAIN" in block and \
           "android.intent.category.LAUNCHER" in block:
            nm = re.search(r'android:name="([^"]+)"', block)
            if nm:
                return nm.group(1)
    for block in activity_blocks:
        if "android.intent.action.MAIN" in block:
            nm = re.search(r'android:name="([^"]+)"', block)
            if nm:
                return nm.group(1)
    return None


def _class_to_smali_path(decompiled_dir: str, class_name: str):
    class_name = class_name.lstrip(".").rstrip(";")
    if class_name.startswith("L"):
        class_name = class_name[1:]
    rel = class_name.replace(".", "/") + ".smali"
    for base in ("smali", "smali_classes2", "smali_classes3"):
        p = os.path.join(decompiled_dir, base, rel)
        if os.path.exists(p):
            return p
    for root, _, files in os.walk(decompiled_dir):
        if os.path.basename(root).startswith("smali"):
            candidate = os.path.join(root, rel)
            if os.path.exists(candidate):
                return candidate
    return None


def _str_to_smali_format(s: str):
    out = []
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ord(ch) < 32 or ord(ch) > 126:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _remove_patterns_in_smali(decompiled_dir, label, patterns, replacements) -> dict:
    report = {"label": label, "files_scanned": 0, "files_modified": 0,
              "matches": 0, "detail": ""}

    compiled_patterns = [re.compile(p) for p in patterns]
    compiled_replacements = [(re.compile(p), r) for p, r in replacements]

    for root, dirs, files in os.walk(decompiled_dir):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            path = os.path.join(root, fname)
            report["files_scanned"] += 1

            content = open(path, encoding="utf-8", errors="ignore").read()
            new_content = content
            matched = False

            for pat in compiled_patterns:
                if pat.search(content):
                    matched = True
                    report["matches"] += 1

            for pat, repl in compiled_replacements:
                new_content = pat.sub(repl, new_content)

            if new_content != content:
                open(path, "w", encoding="utf-8").write(new_content)
                report["files_modified"] += 1

    if report["matches"] == 0:
        report["detail"] = f"{label}: pa gen okenn patwòn jwenn"
    else:
        report["detail"] = (
            f"{label}: {report['matches']} matche, "
            f"{report['files_modified']} fichye modifye"
        )
    return report


def _patch_boolean_methods(content: str, method_re) -> str:
    return _rewrite_method_bodies(content, method_re, "b")


def _patch_credit_methods(content: str, method_re) -> str:
    return _rewrite_method_bodies(content, method_re, "c")


def _rewrite_method_bodies(content: str, method_re, kind: str) -> str:
    method_starts = [m.start() for m in re.finditer(r'^\.method\b', content, re.MULTILINE)]
    if not method_starts:
        return content

    parts = []
    last_end = 0
    for i, start in enumerate(method_starts):
        end_match = re.search(r'^\.end method', content[start:], re.MULTILINE)
        if not end_match:
            parts.append(content[last_end:])
            last_end = len(content)
            break
        end_abs = start + end_match.end()

        prelude = content[last_end:start]
        parts.append(prelude)

        method_block = content[start:end_abs]

        sig_line_end = method_block.find("\n")
        sig_line = method_block if sig_line_end == -1 else method_block[:sig_line_end]
        if method_re.search(sig_line):
            locals_match = re.search(r'\.locals (\d+)', method_block)
            new_body = ""
            if locals_match:
                new_body += f"    .locals {locals_match.group(1)}\n"
            if kind == "b":
                new_body += "    const/4 v0, 0x1\n    return v0"
            else:
                new_body += "    const v0, 0x7fffffff\n    return v0"
            parts.append(sig_line + "\n" + new_body + "\n.end method")
        else:
            parts.append(method_block)

        last_end = end_abs

    if last_end < len(content):
        parts.append(content[last_end:])

    return "".join(parts)


def _count_new_markers(old_content: str, new_content: str) -> int:
    old_returns = old_content.count("    const/4 v0, 0x1\n    return v0") + \
        old_content.count("    const v0, 0x7fffffff\n    return v0")
    new_returns = new_content.count("    const/4 v0, 0x1\n    return v0") + \
        new_content.count("    const v0, 0x7fffffff\n    return v0")
    return max(0, new_returns - old_returns)


def list_patches_applied(patch_results: dict) -> list:
    lines = []
    for key, rep in patch_results.items():
        if not rep:
            continue
        detail = rep.get("detail", "")
        if detail:
            lines.append("• " + detail)
        else:
            n = rep.get("files_modified", 0)
            lines.append(f"• {rep.get('label', key)}: {n} fichye modifye")
    return lines
