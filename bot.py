# -*- coding: utf-8 -*-
"""
bot.py — Bot Telegram APK Modder (prensipal).

Flow konvèsasyon (estaj pa itilizatè):
  START -> /start montre meni
  -> itilizatè voye yon .apk -> nou dekonpile l -> nou mande konfigirasyon
  -> itilizatè voye non / imèl / telefòn (validation)
  -> itilizatè chwazi patche obligatwa ak opsyonèl atravè meni inline
  -> nou aplike patch yo, rekonstwi, siyen, epi voye APK tounen.

Kouri ak long polling (okenn webhook nesesè).
"""
import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import config
import apk_ops
import patcher
import state as state_mod
from utils import (
    is_valid_email,
    is_valid_phone,
    sanitize_filename,
    safe_remove,
    verify_apk,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =============================================================================
# Eta konvèsasyon (ConversationHandler)
# =============================================================================
(
    WAIT_APK,
    WAIT_NAME,
    WAIT_EMAIL,
    WAIT_PHONE,
    WAIT_PATCH_SELECT,
) = range(5)

SKIP = "skip"


def _work_root(user_id: int) -> str:
    root = os.path.join(config.WORK_DIR, str(user_id))
    os.makedirs(root, exist_ok=True)
    return root


def _download_apk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    doc = update.message.document
    if doc is None:
        raise ValueError("Pa gen dokiman")

    if not doc.file_name.lower().endswith(".apk"):
        raise ValueError("Fichye a pa gen ekstansyon .apk")

    if doc.file_size and doc.file_size > config.MAX_APK_SIZE:
        raise ValueError(
            f"Fichye twò gran ({doc.file_size // (1024*1024)} MB). "
            f"Limit se {config.MAX_APK_SIZE // (1024*1024)} MB."
        )

    upload_root = os.path.join(config.UPLOAD_DIR, str(update.effective_user.id))
    os.makedirs(upload_root, exist_ok=True)

    safe_name = sanitize_filename(doc.file_name)
    local_path = os.path.join(upload_root, safe_name)

    f = await doc.get_file()
    await f.download_to_drive(custom_path=local_path)
    return local_path


async def _send_long(update: Update, text: str):
    MAX = 4000
    if len(text) <= MAX:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    for i in range(0, len(text), MAX):
        await update.message.reply_text(text[i:i + MAX], parse_mode=ParseMode.HTML)


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 <b>APK Mod Bot</b>\n\n"
        f"Bonjou {_esc(user.first_name)}! Mwen ka modifye fichye APK "
        f"(pou tès sou pwogram ou posede).\n\n"
        f"<b>Sa mwen ka fè:</b>\n"
        f"• Chanje non aplikasyon an\n"
        f"• Enjekte imèl &amp; telefòn kòm resous\n"
        f"• Ajoute notifikasyon Toast nan lanm nan aplikasyon an\n"
        f"• Patch opsyonèl: retire LVL, ads, root deteksyon, verifikasyon siyati, "
        f"debloke plan/kredi/token\n\n"
        f"👉 Voye yon fichye <b>.apk</b> pou kòmanse.",
        parse_mode=ParseMode.HTML,
    )
    state_mod.clear_state(user.id)
    return WAIT_APK


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 <b>Kijan pou itilize:</b>\n\n"
        "1. Voye yon fichye <code>.apk</code>\n"
        "2. Swiv enstriksyon yo — bay non, imèl, telefòn\n"
        "3. Chwazi patche ou vle aplikasyon an\n"
        "4. Resevwa APK modifye a tounen\n\n"
        "Kòmand: /start — kòmanse, /cancel — anile",
        parse_mode=ParseMode.HTML,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state_mod.clear_state(uid)
    safe_remove(_work_root(uid))
    safe_remove(os.path.join(config.UPLOAD_DIR, str(uid)))
    await update.message.reply_text("❌ Operasyon anile. Voye yon nouvo .apk pou rekòmanse.")
    return ConversationHandler.END


async def receive_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = update.effective_user

    safe_remove(_work_root(uid))

    try:
        apk_path = await _download_apk(update, context)
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return WAIT_APK
    except Exception as e:
        logger.exception("telechajman echwe")
        await update.message.reply_text("⚠️ Telechajman echwe. Re-ese ankò.")
        return WAIT_APK

    await update.message.reply_text("⏳ Dekonpilasyon an kouri... sa ka pran kèk minit.")
    try:
        project_dir = apk_ops.decompile(apk_path, _work_root(uid))
    except apk_ops.ApkBuildError as e:
        await _send_long(update, "❌ Dekonpilasyon echwe:\n" + _esc(str(e)))
        return WAIT_APK
    except Exception as e:
        logger.exception("dekonpilasyon")
        await update.message.reply_text("❌ Erè inatandi pandan dekonpilasyon.")
        return WAIT_APK

    state_mod.set_state(uid, {
        "project_dir": project_dir,
        "apk_name": os.path.splitext(os.path.basename(apk_path))[0],
        "email": None,
        "phone": None,
        "new_name": None,
        "patches": set(),
    })

    await update.message.reply_text(
        "✅ Dekonpilasyon reyisi!\n\n"
        "Kounye a nou pral konfigure modifikasyon yo.\n\n"
        "1️⃣ <b>Non aplikasyon an:</b> ekri nouvo non an (oswa /skip pou pa chanje).",
        parse_mode=ParseMode.HTML,
    )
    return WAIT_NAME


async def ask_email_after_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    if text.lower() in ("/skip", "skip"):
        state_mod.update_state(uid, new_name=None)
    else:
        if len(text) > 60:
            await update.message.reply_text("⚠️ Non twò long (max 60). Re-ese.")
            return WAIT_NAME
        state_mod.update_state(uid, new_name=text)

    await update.message.reply_text(
        "2️⃣ <b>Imèl:</b> ekri adrès imèl la (oswa /skip).\n"
        "<i>Egz: mwen@egzanp.com</i>",
        parse_mode=ParseMode.HTML,
    )
    return WAIT_EMAIL


async def ask_phone_after_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    if text.lower() in ("/skip", "skip"):
        state_mod.update_state(uid, email=None)
    else:
        if not is_valid_email(text):
            await update.message.reply_text(
                "⚠️ Imèl pa valab. Ekri yon imèl valab (oswa /skip)."
            )
            return WAIT_EMAIL
        state_mod.update_state(uid, email=text)

    await update.message.reply_text(
        "3️⃣ <b>Telefòn:</b> ekri nimewo telefòn la (oswa /skip).\n"
        "<i>Egz: +509 1234 5678</i>",
        parse_mode=ParseMode.HTML,
    )
    return WAIT_PHONE


async def show_patch_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    if text.lower() in ("/skip", "skip"):
        state_mod.update_state(uid, phone=None)
    else:
        if not is_valid_phone(text):
            await update.message.reply_text(
                "⚠️ Telefòn pa valab. Ekri yon nimewo valab (oswa /skip)."
            )
            return WAIT_PHONE
        state_mod.update_state(uid, phone=text)

    st = state_mod.get_state(uid)
    summary = (
        f"📋 <b>Rezime konfigirasyon:</b>\n"
        f"• Non: {_esc(st.get('new_name') or '— (pa chanje)')}\n"
        f"• Imèl: {_esc(st.get('email') or '—')}\n"
        f"• Telefòn: {_esc(st.get('phone') or '—')}\n\n"
        f"Kounye a chwazi patche opsyonèl yo (tap pou aktive/desaktive), "
        f"epi klike <b>✅ Konfime</b>."
    )

    keyboard = _patch_keyboard(st)
    await update.message.reply_text(summary, parse_mode=ParseMode.HTML,
                                    reply_markup=keyboard)
    return WAIT_PATCH_SELECT


PATCH_OPTIONS = [
    ("toggle_lvl", "🧾 Retire Google LVL lisans"),
    ("toggle_ads", "📢 Retire SDK anons"),
    ("toggle_root", "🪪 Retire root deteksyon"),
    ("toggle_sig", "🔐 Retire verifikasyon siyati"),
    ("toggle_plan", "💎 Debloke plan/kredi/token (VIP)"),
]


def _patch_keyboard(st: dict) -> InlineKeyboardMarkup:
    patches = st.get("patches", set())
    rows = []
    for key, label in PATCH_OPTIONS:
        active = "✅ " if key.replace("toggle_", "") in patches else "➖ "
        rows.append([
            InlineKeyboardButton(
                active + label,
                callback_data=key,
            )
        ])
    rows.append([
        InlineKeyboardButton("✅ KONFIME & KONSTWI", callback_data="confirm")
    ])
    rows.append([
        InlineKeyboardButton("❌ Anile", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(rows)


async def toggle_patch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    st = state_mod.get_state(uid)
    patches = set(st.get("patches", set()))

    data = query.data
    if data == "confirm":
        await _process_build(update, context, st)
        return ConversationHandler.END
    elif data == "cancel":
        state_mod.clear_state(uid)
        safe_remove(_work_root(uid))
        safe_remove(os.path.join(config.UPLOAD_DIR, str(uid)))
        await query.edit_message_text("❌ Anile. Voye yon nouvo .apk pou rekòmanse.")
        return ConversationHandler.END

    key = data.replace("toggle_", "")
    if key in patches:
        patches.discard(key)
    else:
        patches.add(key)

    st["patches"] = patches
    state_mod.set_state(uid, st)

    await query.edit_message_reply_markup(reply_markup=_patch_keyboard(st))
    return WAIT_PATCH_SELECT


async def _process_build(update: Update, context: ContextTypes.DEFAULT_TYPE, st: dict):
    query = update.callback_query
    uid = query.from_user.id

    await query.edit_message_text("⚙️ Aplike modifikasyon yo... sa ka pran kèk minit.")

    project_dir = st.get("project_dir")
    strings_file = os.path.join(project_dir, "res", "values", "strings.xml")

    report_lines = []
    errors = []

    if st.get("new_name"):
        rep = patcher.change_app_name(
            project_dir, st["new_name"], strings_file
        )
        report_lines.append(("Non", rep["detail"] if rep.get("label_changed")
                             else "Label pa chanje"))

    custom = {}
    if st.get("new_name"):
        custom["mod_name"] = st["new_name"]
    if st.get("email"):
        custom["mod_email"] = st["email"]
    if st.get("phone"):
        custom["mod_phone"] = st["phone"]
    if custom:
        rep = patcher.inject_custom_strings(strings_file, custom)
        report_lines.append(("Resous", rep["detail"]))

    toast_msg = "Modded by APK Mod Bot"
    try:
        rep = patcher.inject_toast(project_dir, toast_msg)
        report_lines.append(("Toast", rep["detail"]))
    except Exception as e:
        logger.exception("toast")
        report_lines.append(("Toast", f"echwe: {e}"))

    patches = st.get("patches", set())
    if "lvl" in patches:
        report_lines.append(("LVL", patcher.remove_lvl(project_dir)["detail"]))
    if "ads" in patches:
        report_lines.append(("ADS", patcher.remove_ads(project_dir)["detail"]))
    if "root" in patches:
        report_lines.append(("ROOT", patcher.remove_root_detection(project_dir)["detail"]))
    if "sig" in patches:
        report_lines.append(("SIGNATURE", patcher.remove_signature_check(project_dir)["detail"]))
    if "plan" in patches:
        report_lines.append(("PLAN/CREDIT/TOKEN", patcher.patch_plan_credit_token(project_dir)["detail"]))

    apk_base = st.get("apk_name", "modded")
    ok, final_apk, msg = apk_ops.full_build_pipeline(
        project_dir, _work_root(uid), apk_base
    )

    if not ok:
        await query.edit_message_text(
            "❌ Konpilasyon echwe:\n" + _esc(msg)
        )
        return ConversationHandler.END

    vok, vmsg = verify_apk(final_apk)

    report = "<b>📦 Modifikasyon konplè!</b>\n\n"
    report += "<b>Modifikasyon:</b>\n"
    for label, detail in report_lines:
        report += f"• <b>{_esc(label)}</b>: {_esc(str(detail))}\n"
    if not report_lines:
        report += "• <i>(okenn modifikasyon — APK rekonstwi &amp; siyen sèlman)</i>\n"
    report += f"\n<b>Siyati:</b> {_esc(vmsg)}\n"

    await query.message.reply_text(report, parse_mode=ParseMode.HTML)
    with open(final_apk, "rb") as f:
        await query.message.reply_document(
            document=f,
            filename=apk_base + "_mod.apk",
            caption="✅ APK modifye a — pare pou enstale!",
        )

    safe_remove(_work_root(uid))
    safe_remove(os.path.join(config.UPLOAD_DIR, str(uid)))
    state_mod.clear_state(uid)


def main():
    if config.BOT_TOKEN.startswith("PASTE") or config.BOT_TOKEN == "":
        raise SystemExit(
            "❌ Ou dwe ranpli BOT_TOKEN nan config.py (oswa varyab BOT_TOKEN)."
        )

    for d in (config.WORK_DIR, config.UPLOAD_DIR, config.STATE_DIR):
        os.makedirs(d, exist_ok=True)

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_APK: [
                MessageHandler(
                    filters.Document.ALL & (~filters.COMMAND),
                    receive_apk,
                ),
            ],
            WAIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email_after_name),
            ],
            WAIT_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone_after_email),
            ],
            WAIT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, show_patch_menu),
            ],
            WAIT_PATCH_SELECT: [
                CallbackQueryHandler(toggle_patch),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_cmd))

    logger.info("Bot debloke... long polling ak kòmanse.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
