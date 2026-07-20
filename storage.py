# -*- coding: utf-8 -*-
"""
storage.py — JSON asosidagi oddiy, xavfsiz ma'lumot saqlash qatlami.

Eski koddagi asosiy muammo: bir nechta turli joyларда load_json/save_json
qayta-qayta e'lon qilingan va bir-birini ustiga yozib, xatolarga sabab
bo'lgan edi. Endi butun loyihada FAQAT shu yerdagi bitta JSONStore
klassi ishlatiladi.
"""
import json
import asyncio
from pathlib import Path


class JSONStore:
    """Diskga yoziladigan oddiy kalit-qiymat ombori (async-xavfsiz)."""

    def __init__(self, path: Path, default: dict):
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self.data = self._load(default)

    def _load(self, default: dict) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(
                json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return json.loads(json.dumps(default))
        try:
            raw = self.path.read_text(encoding="utf-8")
            loaded = json.loads(raw)
            if not isinstance(loaded, dict):
                return json.loads(json.dumps(default))
            # yetishmayotgan kalitlarni to'ldirish (eski fayllar bilan moslik uchun)
            for k, v in default.items():
                loaded.setdefault(k, v)
            return loaded
        except Exception:
            return json.loads(json.dumps(default))

    async def save(self):
        async with self._lock:
            tmp_path = self.path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            tmp_path.replace(self.path)


# ==================== OMBORLAR ====================
from config import DATA_FILE, ADS_FILE, PAYMENTS_FILE  # noqa: E402

users_store = JSONStore(DATA_FILE, {"users": {}, "admin_notifs": {}, "ad_counter": 0})
ads_store = JSONStore(ADS_FILE, {"driver": {}, "passenger": {}})
payments_store = JSONStore(PAYMENTS_FILE, {"payments": {}, "payment_notifs": {}})


DEFAULT_USER = {
    "full_name": "",
    "username": "",
    "phone": None,
    "driver_status": "none",       # none | pending | approved | rejected
    "driver_paused": True,
    "subscription": {
        "tariff": None,
        "start": None,
        "end": None,               # None = umrbod yoki obuna yo'q
        "active": False,
        "reminded_3d": False,
        "reminded_expired": False,
    },
    "last_ad": {},                 # oxirgi e'lon matni/rasmi (qayta ishlatish uchun)
}


def get_user(uid: str) -> dict:
    """Foydalanuvchi yozuvini qaytaradi, yo'q bo'lsa yaratadi."""
    users = users_store.data["users"]
    if uid not in users:
        users[uid] = json.loads(json.dumps(DEFAULT_USER))
    else:
        # eski yozuvlarda yetishmayotgan maydonlarni to'ldirish
        _deep_fill(users[uid], DEFAULT_USER)
    return users[uid]


def _deep_fill(target: dict, defaults: dict):
    for k, v in defaults.items():
        if k not in target:
            target[k] = json.loads(json.dumps(v))
        elif isinstance(v, dict) and isinstance(target.get(k), dict):
            _deep_fill(target[k], v)


def touch_user_profile(uid: str, full_name: str, username: str):
    """Foydalanuvchining ism/username ma'lumotini yangilab boradi."""
    u = get_user(uid)
    u["full_name"] = full_name or u.get("full_name") or ""
    u["username"] = username or u.get("username") or ""


async def save_users():
    await users_store.save()


async def save_ads():
    await ads_store.save()


async def save_payments():
    await payments_store.save()


def next_ad_number() -> int:
    """Yo'lovchi e'lonlari uchun ketma-ket raqam (#01, #02, ...)."""
    users_store.data["ad_counter"] = users_store.data.get("ad_counter", 0) + 1
    return users_store.data["ad_counter"]
