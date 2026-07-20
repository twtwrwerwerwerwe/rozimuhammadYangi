# -*- coding: utf-8 -*-
"""
bot_instance.py — Bot va Dispatcher ning YAGONA nusxasi.

Eski koddagi muammolardan biri: bot/dp turli joylarda qayta-qayta
yaratilishi mumkin edi. Endi butun loyihada faqat shu yerdagi bitta
`bot` va `dp` obyekti ishlatiladi — barcha handler fayllari shu yerdan
import qiladi.
"""
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
