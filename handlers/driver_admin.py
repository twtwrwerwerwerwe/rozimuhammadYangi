# -*- coding: utf-8 -*-
"""
handlers/driver_admin.py — haydovchilik arizalarini admin tomonidan
tasdiqlash/rad etish va tasdiqlangan haydovchilar ro'yxati.
"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot_instance import bot, dp
from config import ADMINS
from storage import get_user, save_users, users_store
from states import DriverStates
from utils import display_name
from keyboards import (
    driver_apply_kb, back_kb, main_menu,
    admin_driver_decision_kb, admin_driver_manage_kb, phone_request_kb,
)


async def notify_admins_new_application(message: types.Message, uid: str):
    kb = admin_driver_decision_kb(uid)
    username = message.from_user.username
    username_display = f"@{username}" if username else "—"
    notifs = []
    for admin in ADMINS:
        try:
            msg = await bot.send_message(
                admin,
                f"🚘 <b>Yangi haydovchilik arizasi</b>\n\n"
                f"👤 Ism: <b>{message.from_user.full_name}</b>\n"
                f"🔗 Username: {username_display}\n"
                f"🆔 ID: <code>{uid}</code>",
                reply_markup=kb,
            )
            notifs.append({"admin": admin, "msg_id": msg.message_id})
        except Exception:
            pass
    users_store.data["admin_notifs"][uid] = notifs
    await save_users()


@dp.message_handler(lambda m: m.text == "🚘 Haydovchi", state="*")
async def driver_section(message: types.Message, state: FSMContext):
    await state.finish()
    uid = str(message.from_user.id)
    u = get_user(uid)

    if message.from_user.id in ADMINS:
        if u["driver_status"] != "approved":
            u["driver_status"] = "approved"
            u["driver_paused"] = False
            u["subscription"]["active"] = True
        await save_users()
        from keyboards import driver_main_kb
        return await message.answer("Haydovchi bo‘limi (admin):", reply_markup=driver_main_kb())

    status = u["driver_status"]
    if status in ("none", "rejected"):
        text = "Siz hali haydovchi emassiz. Ariza yuboring." if status == "none" \
            else "❌ Admin arizangizni rad etgan edi. Xohlasangiz qayta ariza yuborishingiz mumkin."
        return await message.answer(text, reply_markup=driver_apply_kb())

    if status == "pending":
        return await message.answer("⏳ Arizangiz admin tomonidan ko‘rib chiqilmoqda…", reply_markup=back_kb())

    # status == approved
    if not u.get("phone"):
        await state.set_state(DriverStates.waiting_phone)
        return await message.answer(
            "📱 Iltimos, telefon raqamingizni yuboring.\n"
            "Tugma orqali yoki qo‘lda kiritishingiz mumkin (masalan: 901234567).",
            reply_markup=phone_request_kb(),
        )

    if not u["subscription"].get("active"):
        from handlers.payment import show_tariffs
        return await show_tariffs(message)

    from keyboards import driver_main_kb
    await message.answer("Haydovchi bo‘limi:", reply_markup=driver_main_kb())


@dp.message_handler(lambda m: m.text == "📨 Haydovchi bo‘lish uchun ariza yuborish")
async def driver_apply(message: types.Message):
    uid = str(message.from_user.id)
    u = get_user(uid)

    if u["driver_status"] == "pending":
        return await message.answer("Siz allaqachon ariza yuborgansiz. Iltimos kuting.", reply_markup=back_kb())
    if u["driver_status"] == "approved":
        from keyboards import driver_main_kb
        return await message.answer("Siz allaqachon tasdiqlangan haydovchisiz.", reply_markup=driver_main_kb())

    u["driver_status"] = "pending"
    u["driver_paused"] = True
    u["full_name"] = message.from_user.full_name or u.get("full_name", "")
    u["username"] = message.from_user.username or u.get("username", "")
    await save_users()

    await notify_admins_new_application(message, uid)
    await message.answer("✅ Arizangiz adminga yuborildi! ⏳ Iltimos, javobini kuting.", reply_markup=back_kb())


@dp.callback_query_handler(lambda c: c.data and c.data.split(":")[0] in
                            ("drv_ok", "drv_no", "drv_view", "drv_remove", "drv_keep"))
async def admin_driver_action(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return await call.answer("Faqat adminlar uchun.", show_alert=True)

    action, _, uid = call.data.partition(":")
    if not uid:
        return await call.answer("Xatolik.", show_alert=True)

    u = get_user(uid)

    if action == "drv_ok":
        u["driver_status"] = "approved"
        u["driver_paused"] = True
        await save_users()
        await _update_admin_notifs(uid, "✅ Amal bajarildi (tasdiqlandi)")

        # haydovchidan telefon raqamini so'raymiz
        try:
            state = dp.current_state(chat=int(uid), user=int(uid))
            await state.set_state(DriverStates.waiting_phone)
            await bot.send_message(
                int(uid),
                "🎉 Admin sizni haydovchi sifatida tasdiqladi!\n\n"
                "📱 Endi telefon raqamingizni yuboring — tugma orqali yoki qo‘lda "
                "(masalan: 901234567).",
                reply_markup=phone_request_kb(),
            )
        except Exception:
            pass
        await call.answer("Tasdiqlandi ✅")

    elif action == "drv_no":
        u["driver_status"] = "rejected"
        u["driver_paused"] = True
        await save_users()
        await _update_admin_notifs(uid, "❌ Amal bajarildi (rad etildi)")
        try:
            await bot.send_message(
                int(uid),
                "❌ Admin arizangizni rad etdi. Xohlasangiz qayta ariza yuborishingiz mumkin.",
                reply_markup=main_menu(),
            )
        except Exception:
            pass
        await call.answer("Rad etildi ❌")

    elif action == "drv_view":
        name = display_name(u, uid)
        sub = u.get("subscription", {})
        sub_text = "faol ✅" if sub.get("active") else "faol emas ❌"
        txt = (
            f"🚘 <b>Haydovchi ma'lumotlari</b>\n\n"
            f"👤 Ism: <b>{name}</b>\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📞 Telefon: {u.get('phone') or '—'}\n"
            f"📋 Status: {u.get('driver_status', '—')}\n"
            f"💳 Obuna: {sub_text}"
        )
        await bot.send_message(call.from_user.id, txt, reply_markup=admin_driver_manage_kb(uid))
        await call.answer()

    elif action == "drv_remove":
        u["driver_status"] = "rejected"
        u["driver_paused"] = True
        u["subscription"]["active"] = False
        await save_users()
        await call.answer("Foydalanuvchi chiqarib tashlandi.")
        try:
            await bot.send_message(int(uid), "❌ Siz haydovchilar ro‘yxatidan chiqarib tashlandingiz.", reply_markup=main_menu())
        except Exception:
            pass

    elif action == "drv_keep":
        u["driver_status"] = "approved"
        await save_users()
        await call.answer("Foydalanuvchi haydovchi sifatida qoldirildi.")
        try:
            from keyboards import driver_main_kb
            await bot.send_message(int(uid), "✅ Siz haydovchi sifatida qoldirildingiz.", reply_markup=driver_main_kb())
        except Exception:
            pass


async def _update_admin_notifs(uid: str, new_text: str):
    notifs = users_store.data.get("admin_notifs", {}).get(uid, [])
    for item in notifs:
        try:
            await bot.edit_message_text(new_text, item["admin"], item["msg_id"])
        except Exception:
            pass


@dp.message_handler(lambda m: m.text == "👥 Haydovchilar")
async def admin_drivers_list(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("Faqat adminlar uchun.")

    kb = types.InlineKeyboardMarkup()
    found = False
    for uid, u in users_store.data["users"].items():
        if u.get("driver_status") == "approved":
            kb.add(types.InlineKeyboardButton(display_name(u, uid), callback_data=f"drv_view:{uid}"))
            found = True
    if not found:
        return await message.answer("Hozircha tasdiqlangan haydovchilar yo‘q.")
    await message.answer("📋 Tasdiqlangan haydovchilar ro‘yxati:", reply_markup=kb)
