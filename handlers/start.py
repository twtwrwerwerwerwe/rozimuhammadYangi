# -*- coding: utf-8 -*-
"""handlers/start.py — /start buyrug'i va umumiy 'Orqaga' tugmasi."""
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot_instance import dp
from config import ADMINS
from storage import get_user, touch_user_profile, save_users
from keyboards import main_menu


@dp.message_handler(commands=["start"], state="*")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.finish()
    uid = str(message.from_user.id)
    touch_user_profile(uid, message.from_user.full_name or "", message.from_user.username or "")
    await save_users()

    is_admin = message.from_user.id in ADMINS
    args = message.get_args()

    if args == "zakaz":
        await message.answer(
            "🚕 Marhamat! Agar yo‘lovchi bo‘lsangiz, "
            "quyidagi <b>🧍 Yo‘lovchi</b> bo‘limidan buyurtma berishingiz mumkin.",
            reply_markup=main_menu(is_admin=is_admin),
        )
        return

    await message.answer(
        "<b>Assalomu alaykum! 👋</b>\n\nSiz kimsiz? Tanlang:",
        reply_markup=main_menu(is_admin=is_admin),
    )


async def do_back(message: types.Message, state: FSMContext):
    """Har qanday holatdan asosiy menyuga qaytarish (boshqa modullardan ham chaqiriladi)."""
    await state.finish()
    uid = str(message.from_user.id)
    get_user(uid)
    is_admin = message.from_user.id in ADMINS
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu(is_admin=is_admin))


@dp.message_handler(lambda m: m.text == "◀️ Orqaga", state="*")
async def go_back(message: types.Message, state: FSMContext):
    await do_back(message, state)
