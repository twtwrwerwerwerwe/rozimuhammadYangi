# -*- coding: utf-8 -*-
"""keyboards.py — barcha klaviaturalar shu yerda, bitta joyda."""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import TARIFFS, AD_INTERVALS, PASSENGER_ROUTES, BOT_USERNAME, ADMIN_USERNAME

BACK = "◀️ Orqaga"


# ==================== ASOSIY MENYU ====================
def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🚘 Haydovchi"), KeyboardButton("🧍 Yo‘lovchi"))
    if is_admin:
        kb.add(KeyboardButton("👥 Haydovchilar"), KeyboardButton("💳 To‘lovlar"))
    return kb


def back_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(BACK)
    return kb


# ==================== HAYDOVCHI ====================
def driver_apply_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📨 Haydovchi bo‘lish uchun ariza yuborish")
    kb.add(BACK)
    return kb


def phone_request_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamni tugma orqali yoki qo'lda yuborish imkoniyati."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Raqamni yuborish", request_contact=True))
    kb.add(BACK)
    return kb


def driver_main_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📣 E’lon berish", "⏸ To‘xtatish")
    kb.add("🆕 Yangi e’lon", "💳 Mening obunam")
    kb.add(BACK)
    return kb


def interval_inline_kb() -> InlineKeyboardMarkup:
    """E'lon necha daqiqada yuborilishini tanlash — endi inline tugma
    sifatida xabar ostida chiqadi (yozish maydonini bosib turmaydi)."""
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(*[
        InlineKeyboardButton(f"{m} daqiqa", callback_data=f"ad_interval:{m}")
        for m in AD_INTERVALS
    ])
    return kb


def ad_confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash va yuborish", callback_data="ad_confirm"),
        InlineKeyboardButton("🗑 Bekor qilish", callback_data="ad_cancel"),
    )
    return kb


def driver_channel_ad_kb(phone: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if phone:
        kb.add(InlineKeyboardButton("📞 Haydovchiga qo‘ng‘iroq", url=f"tel:{phone}"))
    kb.add(InlineKeyboardButton(
        "📩 Zakaz berish", url=f"https://t.me/{BOT_USERNAME}?start=zakaz"
    ))
    return kb


# ==================== ADMIN — HAYDOVCHI TASDIQLASH ====================
def admin_driver_decision_kb(uid: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"drv_ok:{uid}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"drv_no:{uid}"),
    )
    return kb


def admin_driver_manage_kb(uid: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("❌ Chiqarib tashlash", callback_data=f"drv_remove:{uid}"),
        InlineKeyboardButton("✅ Qoldirish", callback_data=f"drv_keep:{uid}"),
    )
    return kb


# ==================== TO'LOV / TARIFLAR ====================
def tariff_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for key, t in TARIFFS.items():
        price = f"{t['price']:,}".replace(",", " ")
        kb.add(InlineKeyboardButton(
            f"{t['label']} — {price} so‘m", callback_data=f"tariff:{key}"
        ))
    return kb


def payment_method_kb(tariff_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("👨‍💼 Admin orqali murojaat", callback_data=f"pm:admin:{tariff_key}"))
    kb.add(InlineKeyboardButton("💳 Click / Payme", callback_data=f"pm:click:{tariff_key}"))
    kb.add(InlineKeyboardButton("🧾 Chek orqali to‘lov", callback_data=f"pm:receipt:{tariff_key}"))
    kb.add(InlineKeyboardButton("⬅️ Orqaga (tarif tanlash)", callback_data="pm:back"))
    return kb


def admin_payment_decision_kb(payment_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"pay_ok:{payment_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"pay_no:{payment_id}"),
    )
    return kb


def contact_admin_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"✍️ {ADMIN_USERNAME} bilan yozishish", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
    return kb


# ==================== YO'LOVCHI ====================
def passenger_entry_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚖 Haydovchi chaqirish")
    kb.add(BACK)
    return kb


def route_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for r in PASSENGER_ROUTES:
        kb.add(f"🚗 {r}")
    kb.add("✍️ O‘zim yozaman", BACK)
    return kb


def location_choice_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("➡️ Lokatsiyasiz davom etish")
    kb.add(BACK)
    return kb


def passenger_channel_kb(ad_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("👁 E’lonni ko‘rish", callback_data=f"view_pass:{ad_id}"))
    return kb


def passenger_channel_taken_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Qabul qilindi", callback_data="taken"))
    return kb


def passenger_ad_full_kb(ad_id: str, has_location: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Qabul qilish", callback_data=f"take_pass:{ad_id}"))
    if has_location:
        kb.add(InlineKeyboardButton("📍 Lokatsiyani ochish", callback_data=f"open_loc:{ad_id}"))
    return kb


def map_choice_kb(ad_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🗺 Google Maps", callback_data=f"maplink:google:{ad_id}"))
    kb.add(InlineKeyboardButton("🗺 Yandex Maps", callback_data=f"maplink:yandex:{ad_id}"))
    kb.add(InlineKeyboardButton("🗺 2GIS", callback_data=f"maplink:2gis:{ad_id}"))
    return kb


def open_map_link_kb(url: str, label: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"📍 {label}da ochish", url=url))
    return kb


def driver_profile_kb(username: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    if username:
        kb.add(InlineKeyboardButton("👤 Haydovchi profili", url=f"https://t.me/{username}"))
    return kb


def open_in_bot_kb(payload: str = "zakaz") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🤖 Botga o‘tish", url=f"https://t.me/{BOT_USERNAME}?start={payload}"))
    return kb
