# -*- coding: utf-8 -*-
"""
handlers/driver.py — haydovchi telefon raqami, e'lon yaratish
(matn -> rasm -> interval -> tasdiqlash), to'xtatish va obuna holati.
"""
import time
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot_instance import bot, dp
from handlers.start import do_back
from config import ADMINS, DRIVER_CHANNELS
from storage import get_user, save_users, save_ads, ads_store
from states import DriverStates
from utils import normalize_phone, new_id, fmt_date, seconds_to_human
from keyboards import (
    back_kb, main_menu, driver_main_kb, phone_request_kb,
    interval_inline_kb, ad_confirm_kb, driver_channel_ad_kb,
)


# ==================== TELEFON RAQAMNI QABUL QILISH ====================
@dp.message_handler(content_types=["contact", "text"], state=DriverStates.waiting_phone)
async def driver_get_phone(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)

    if message.text == "◀️ Orqaga":
        return await do_back(message, state)

    raw = message.contact.phone_number if message.contact else message.text
    phone = normalize_phone(raw)
    if not phone:
        return await message.answer(
            "❌ Raqam noto‘g‘ri formatda. Iltimos qayta yuboring "
            "(masalan: 901234567 yoki +998901234567).",
            reply_markup=phone_request_kb(),
        )

    u = get_user(uid)
    u["phone"] = phone
    await save_users()
    await state.finish()

    await message.answer(
        f"✅ Raqamingiz saqlandi: <code>{phone}</code>\nEndi bemalol botdan foydalanishingiz mumkin!",
        reply_markup=main_menu(is_admin=message.from_user.id in ADMINS),
    )

    if not u["subscription"].get("active"):
        from handlers.payment import show_tariffs
        await show_tariffs(message)


# ==================== E'LON BERISH (oxirgi e'londan davom etish) ====================
def _driver_ready(u: dict, uid: str = None) -> bool:
    is_admin = uid is not None and int(uid) in ADMINS
    if u.get("driver_status") != "approved":
        return False
    if not u["subscription"].get("active"):
        return False
    if not is_admin and not u.get("phone"):
        return False
    return True


@dp.message_handler(lambda m: m.text == "📣 E’lon berish", state="*")
async def driver_new_ad_continue(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    u = get_user(uid)
    if not _driver_ready(u, uid):
        return await message.answer("❌ Bu funksiyadan foydalanish uchun avval ro‘yxatdan o‘ting.", reply_markup=back_kb())

    u["driver_paused"] = False
    await save_users()

    last_ad = u.get("last_ad") or {}
    if last_ad.get("text") and last_ad.get("photo"):
        await state.update_data(ad_text=last_ad["text"], ad_photo=last_ad["photo"])
        await state.set_state(DriverStates.waiting_ad_photo)  # interval callback shu state'ni kutadi
        await message.answer(
            "♻️ Oxirgi e’loningiz asosida davom etyapmiz (matn va rasm qayta so‘ralmaydi).\n\n"
            "⏱ E’lon necha daqiqada bir marta yuborilsin?",
            reply_markup=interval_inline_kb(),
        )
        return

    await state.update_data(ad_text=None, ad_photo=None)
    await state.set_state(DriverStates.waiting_ad_text)
    await message.answer("✍️ E’lon matnini yuboring:", reply_markup=back_kb())


@dp.message_handler(lambda m: m.text == "🆕 Yangi e’lon", state="*")
async def driver_new_ad_fresh(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    u = get_user(uid)
    if not _driver_ready(u, uid):
        return await message.answer("❌ Bu funksiyadan foydalanish uchun avval ro‘yxatdan o‘ting.", reply_markup=back_kb())

    u["driver_paused"] = False
    await save_users()

    await state.update_data(ad_text=None, ad_photo=None)
    await state.set_state(DriverStates.waiting_ad_text)
    await message.answer("✍️ Yangi e’lon matnini yuboring:", reply_markup=back_kb())


@dp.message_handler(state=DriverStates.waiting_ad_text, content_types=["text"])
async def driver_get_text(message: types.Message, state: FSMContext):
    if message.text == "◀️ Orqaga":
        return await do_back(message, state)
    await state.update_data(ad_text=message.text)
    await state.set_state(DriverStates.waiting_ad_photo)
    await message.answer("📸 Mashina rasmini yuboring (majburiy):", reply_markup=back_kb())


@dp.message_handler(state=DriverStates.waiting_ad_photo, content_types=["photo"])
async def driver_get_photo(message: types.Message, state: FSMContext):
    await state.update_data(ad_photo=message.photo[-1].file_id)
    data = await state.get_data()
    await message.answer(
        f"⏱ E’lon necha daqiqada bir marta yuborilsin?\n\n✍️ Matn: {data.get('ad_text', '')[:200]}",
        reply_markup=interval_inline_kb(),
    )


@dp.message_handler(state=DriverStates.waiting_ad_photo, content_types=["text"])
async def driver_get_photo_wrong_type(message: types.Message, state: FSMContext):
    if message.text == "◀️ Orqaga":
        return await do_back(message, state)
    await message.answer("📸 Iltimos, mashina RASMINI yuboring (matn emas).", reply_markup=back_kb())


@dp.callback_query_handler(lambda c: c.data.startswith("ad_interval:"), state=DriverStates.waiting_ad_photo)
async def driver_pick_interval(call: types.CallbackQuery, state: FSMContext):
    minutes = int(call.data.split(":")[1])
    await state.update_data(ad_interval=minutes)
    data = await state.get_data()

    text_preview = (data.get("ad_text") or "")[:300]
    summary = (
        f"📋 <b>E’lon xulosasi</b>\n\n"
        f"✍️ Matn: {text_preview}\n"
        f"⏱ Interval: {minutes} daqiqa\n\n"
        f"Tasdiqlaysizmi?"
    )
    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass
    await call.message.answer(summary, reply_markup=ad_confirm_kb())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "ad_cancel", state="*")
async def driver_cancel_ad(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass
    await call.message.answer("🗑 Bekor qilindi.", reply_markup=driver_main_kb())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "ad_confirm", state="*")
async def driver_confirm_ad(call: types.CallbackQuery, state: FSMContext):
    uid = str(call.from_user.id)
    data = await state.get_data()
    text = data.get("ad_text")
    photo = data.get("ad_photo")
    interval = data.get("ad_interval", 5)

    if not text or not photo:
        await state.finish()
        return await call.answer("Xatolik: e’lon ma’lumotlari topilmadi. Qaytadan boshlang.", show_alert=True)

    u = get_user(uid)
    ad_id = new_id()
    ads_store.data["driver"][ad_id] = {
        "user": uid,
        "text": text,
        "photo": photo,
        "interval": interval,
        "start": time.time(),
        "active": True,
        "last_sent": 0,
        "reminded_12h": False,
    }
    u["last_ad"] = {"text": text, "photo": photo, "interval": interval}
    u["driver_paused"] = False
    await save_ads()
    await save_users()
    await state.finish()

    await _broadcast_driver_ad(ad_id)

    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass
    await call.message.answer("🚀 E’lon yuborildi va faol holatda!", reply_markup=driver_main_kb())
    await call.answer()


async def _broadcast_driver_ad(ad_id: str):
    ad = ads_store.data["driver"].get(ad_id)
    if not ad:
        return
    user = get_user(ad["user"])
    phone = user.get("phone")
    kb = driver_channel_ad_kb(phone)
    for ch in DRIVER_CHANNELS:
        try:
            await bot.send_photo(ch, ad["photo"], caption=ad["text"], reply_markup=kb)
        except Exception:
            pass
    ad["last_sent"] = time.time()
    await save_ads()


# ==================== TO'XTATISH ====================
@dp.message_handler(lambda m: m.text == "⏸ To‘xtatish", state="*")
async def pause_driver(message: types.Message, state: FSMContext):
    await state.finish()
    uid = str(message.from_user.id)
    u = get_user(uid)
    u["driver_paused"] = True

    changed = False
    for ad in ads_store.data["driver"].values():
        if ad.get("user") == uid and ad.get("active", False):
            ad["active"] = False
            changed = True
    if changed:
        await save_ads()
    await save_users()

    await message.answer("⏸ E’loningiz muvaffaqiyatli to‘xtatildi.", reply_markup=main_menu(is_admin=message.from_user.id in ADMINS))


# ==================== MENING OBUNAM ====================
@dp.message_handler(lambda m: m.text == "💳 Mening obunam", state="*")
async def my_subscription(message: types.Message, state: FSMContext):
    await state.finish()
    uid = str(message.from_user.id)
    u = get_user(uid)
    sub = u.get("subscription", {})

    if not sub.get("active"):
        from handlers.payment import show_tariffs
        return await show_tariffs(message)

    tariff = sub.get("tariff")
    end = sub.get("end")
    if end is None:
        expiry_text = "♾ Umrbod (muddatsiz)"
    else:
        remaining = end - time.time()
        expiry_text = f"{fmt_date(end)} ({seconds_to_human(remaining)} qoldi)" if remaining > 0 else "muddati tugagan"

    await message.answer(
        f"💳 <b>Sizning obunangiz</b>\n\n"
        f"📦 Tarif: {tariff or '—'}\n"
        f"📅 Tugash sanasi: {expiry_text}",
        reply_markup=driver_main_kb(),
    )
