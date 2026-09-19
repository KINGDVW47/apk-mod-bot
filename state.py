# -*- coding: utf-8 -*-
"""
state.py — Jesyon estaj konvèsasyon pou chak itilizatè (JSON fichye).

Chak itilizatè Telegram gen yon fichye JSON separe nan STATE_DIR.
"""
import json
import os
import threading

from config import STATE_DIR

_lock = threading.Lock()


def _state_path(user_id) -> str:
    return os.path.join(STATE_DIR, f"{user_id}.json")


def get_state(user_id) -> dict:
    p = _state_path(user_id)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def set_state(user_id, state: dict):
    os.makedirs(STATE_DIR, exist_ok=True)
    with _lock:
        with open(_state_path(user_id), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)


def update_state(user_id, **kwargs):
    state = get_state(user_id)
    state.update(kwargs)
    set_state(user_id, state)
    return state


def clear_state(user_id):
    p = _state_path(user_id)
    if os.path.exists(p):
        try:
            os.remove(p)
        except OSError:
            pass
