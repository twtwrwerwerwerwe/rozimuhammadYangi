# -*- coding: utf-8 -*-
"""
config.py — Botning barcha sozlamalari shu yerda joylashgan.
Faqat shu faylni tahrirlab, botning token, admin, guruh va narxlarini
o'zgartirishingiz mumkin — boshqa fayllarga tegishning hojati yo'q.
"""
from pathlib import Path

# ==================== BOT ====================
TOKEN = "8474009974:AAERXCF7Jj1Qv-QGixFGaFVIgnUZcoIJoPs"
BOT_USERNAME = "rishtonBogdodToshkentTaxi_bot"  # @ belgisiz

# ==================== ADMIN ====================
ADMINS = [6302873072]                 # admin(lar) telegram ID si
ADMIN_PHONE = "+998952871666"         # admin telefon raqami (foydalanuvchiga ko'rsatiladi)
ADMIN_USERNAME = "@akramjonov777"     # admin telegram username (foydalanuvchiga ko'rsatiladi)

# ==================== GURUH / KANALLAR ====================
DRIVER_CHANNELS = [-1003640341366]     # haydovchilar e'lonlari shu yerga tushadi
PASSENGER_CHANNELS = [-1003888459573]  # yo'lovchilar e'lonlari shu yerga tushadi

# ==================== FAYLLAR ====================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "storage_data"
DATA_FILE = DATA_DIR / "data.json"
ADS_FILE = DATA_DIR / "ads.json"
PAYMENTS_FILE = DATA_DIR / "payments.json"

# ==================== TO'LOV — CHEK ORQALI ====================
# "Chek orqali to'lov" tanlanganda foydalanuvchiga shu karta ko'rsatiladi.
PAYMENT_CARD = {
    "number": "9860080386497343",
    "owner": "Khurriyatxon Ohunjonova",
    "phone": "+998908339210",
}

# ==================== TO'LOV — CLICK / PAYME ====================
# Agar quyidagi merchant ID'lar kiritilmagan (None) bo'lsa, bot foydalanuvchiga
# "Bu to'lov usuli hozircha vaqtinchalik mavjud emas" deb avtomatik xabar beradi.
# Merchant ID'larni sozlagandan so'ng shu yerga kiritsangiz, avto-to'lov ishga tushadi.
CLICK_MERCHANT_ID = None
PAYME_MERCHANT_ID = None

# ==================== TARIFLAR ====================
# key -> {label: ko'rinadigan nom, days: necha kunlik obuna (None = umrbod), price: narxi so'mda}
TARIFFS = {
    "1m": {"label": "1 oylik", "days": 30, "price": 60_000},
    "2m": {"label": "2 oylik", "days": 60, "price": 110_000},
    "5m": {"label": "5 oylik", "days": 150, "price": 250_000},
    "lifetime": {"label": "♾ Umrbod", "days": None, "price": 600_000},
}

# ==================== ESLATMALAR / VAQT SOZLAMALARI ====================
REMINDER_DAYS_BEFORE = 3          # obuna tugashiga necha kun qolganda eslatma yuboriladi
BACKGROUND_LOOP_INTERVAL = 30     # fon jarayoni necha soniyada bir tekshiradi (soniya)

AD_AUTO_STOP_HOURS = 24           # haydovchi e'loni necha soatdan keyin avtomatik to'xtaydi
AD_REMINDER_HOURS = 12            # necha soatdan keyin eslatma yuboriladi (to'xtatilmagan bo'lsa)

# Yo'lovchi yo'nalishlari (eskisi saqlab qolindi)
PASSENGER_ROUTES = [
    "Qo‘qon → Toshkent", "Toshkent → Qo‘qon",
    "Rishton → Toshkent", "Toshkent → Rishton",
    "Buvayda → Toshkent", "Toshkent → Buvayda",
    "Yangi Qo‘rg‘on → Toshkent", "Toshkent → Yangi Qo‘rg‘on",
    "Farg‘ona → Toshkent", "Toshkent → Farg‘ona",
    "Bag‘dod → Toshkent", "Toshkent → Bag‘dod",
]

# Haydovchi e'loni necha daqiqada bir qayta yuborilishi mumkin bo'lgan variantlar
AD_INTERVALS = [5, 10, 15, 20, 30]
