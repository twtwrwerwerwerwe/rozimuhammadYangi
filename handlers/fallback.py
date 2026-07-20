# -*- coding: utf-8 -*-
"""
handlers/fallback.py — "qo'riqchi" handlerlar.

MUHIM: bu fayl handlerlar ro'yxatida ENG OXIRIDA ro'yxatdan o'tishi kerak
(main.py da eng oxirida import qilinadi). Agar biror sabab bilan (masalan,
kutilmagan matn, eskirgan tugma bosilishi va h.k.) boshqa hech qanday
handler mos kelmasa, bot foydalanuvchiga "jim" javob bermaydi — balki
tushunarli xabar bilan asosiy menyuga yo'naltiradi.
"""
from aiogram import types
from aiogram.dispatcher import FSMContext

from bot_instance import dp
from config import ADMINS
from storage import get_user
from keyboards import main_menu


@dp.message_handler(content_types=types.ContentTypes.ANY, state="*")
async def fallback_message(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    get_user(uid)
    await state.finish()
    await message.answer(
        "🤔 Buni tushunmadim. Quyidagi menyudan kerakli bo‘limni tanlang:",
        reply_markup=main_menu(is_admin=message.from_user.id in ADMINS),
    )


@dp.callback_query_handler(lambda c: True, state="*")
async def fallback_callback(call: types.CallbackQuery):
    await call.answer(
        "⏳ Bu tugma eskirgan yoki amal qilmaydi. Iltimos, /start bosing.",
        show_alert=True,
    )
