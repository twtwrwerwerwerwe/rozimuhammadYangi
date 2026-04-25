# taxi_bot_final_fixed.py
import asyncio
import json
import time
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import time
import json
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ---------------- CONFIG ----------------
TOKEN = "8474009974:AAERXCF7Jj1Qv-QGixFGaFVIgnUZcoIJoPs"
ADMINS = [6302873072]
BOT_USERNAME = "@rishtonBogdodToshkentTaxi_bot"

# Bu yerga 1 yoki undan ortiq kanal id larini qo'yishingiz mumkin.
DRIVER_CHANNELS = [-1003322681147]
PASSENGER_CHANNELS = [-1003888459573]

DATA_FILE = Path("data.json")
ADS_FILE = Path("ads.json")

# ---------------- JSON HELPERS ----------------
def load_json(path, default):
    if not path.exists():
        return default
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return default
        # ensure structure for compatibility
        if 'users' not in d:
            d['users'] = {}
        if 'admin_notifs' not in d:
            d['admin_notifs'] = {}  # uid -> list of {"admin": id, "msg_id": id}
        return d
    except:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------- INIT FILES ----------------
if not DATA_FILE.exists():
    save_json(DATA_FILE, {"users":{}, "admin_notifs": {}})
if not ADS_FILE.exists():
    save_json(ADS_FILE, {"driver":{}, "passenger":{}})

# ---------------- BOT ----------------
bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
data = load_json(DATA_FILE, {"users":{}, "admin_notifs": {}})
ads = load_json(ADS_FILE, {"driver":{}, "passenger":{}})


ADS_FILE = "ads.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

ads = load_json(ADS_FILE)


# ---------------- KEYBOARDS ----------------
def main_menu(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🚘 Haydovchi"), KeyboardButton("🧍 Yo‘lovchi"))
    if is_admin:
        kb.add(KeyboardButton("👥 Haydovchilar"))
    return kb

def back_btn():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("◀️ Orqaga")
    return kb

def driver_main_inline():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📣 E’lon berish", callback_data="drv_ad"))
    kb.add(InlineKeyboardButton("⏸ To‘xtatish", callback_data="drv_stop"))
    kb.add(InlineKeyboardButton("🆕 Yangi e’lon", callback_data="drv_new"))
    return kb

# ---------------- START ----------------
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    uid = str(message.from_user.id)
    if uid not in data['users']:
        data['users'][uid] = {
            "role": None,
            "driver_status": "none",
            "driver_paused": False,
            "state": None,
            "driver_temp": {},
            "pass_temp": {},
            "full_name": message.from_user.full_name or "",
            "username": message.from_user.username or ""
        }
        save_json(DATA_FILE, data)
    else:
        # update stored display info on each /start to keep names up-to-date
        data['users'][uid].setdefault("full_name", message.from_user.full_name or "")
        data['users'][uid].setdefault("username", message.from_user.username or "")
        # also refresh with latest values
        data['users'][uid]['full_name'] = message.from_user.full_name or data['users'][uid].get('full_name', '')
        data['users'][uid]['username'] = message.from_user.username or data['users'][uid].get('username', '')
        save_json(DATA_FILE, data)

    is_admin = int(message.from_user.id) in ADMINS
    await message.answer("<b>Salom!</b> Siz kimsiz? Tanlang:", reply_markup=main_menu(is_admin=is_admin))

@dp.message_handler(lambda m: m.text == "🚘 Haydovchi")
async def driver_section(message: types.Message):
    uid = str(message.from_user.id)

    # user yo‘q bo‘lsa yaratamiz
    if uid not in data['users']:
        data['users'][uid] = {
            "role": None,
            "driver_status": "none",
            "driver_paused": False,
            "state": None,
            "driver_temp": {},
            "pass_temp": {},
            "full_name": message.from_user.full_name or "",
            "username": message.from_user.username or ""
        }
        save_json(DATA_FILE, data)

    u = data['users'][uid]

    # 🔴 ADMIN → avtomatik approved
    if int(message.from_user.id) in ADMINS:
        u['driver_status'] = "approved"
        u['driver_paused'] = False
        save_json(DATA_FILE, data)

        return await message.answer(
            "🚘 Haydovchi bo‘limi (admin):",
            reply_markup=driver_main_inline()
        )

    # ❌ hali haydovchi emas
    if u['driver_status'] == "none":
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📨 Ariza yuborish", callback_data="apply_driver")
        )
        return await message.answer(
            "❌ Siz hali haydovchi emassiz",
            reply_markup=kb
        )

    # ⏳ pending
    if u['driver_status'] == "pending":
        return await message.answer("⏳ Arizangiz ko‘rib chiqilmoqda...")

    # ❌ rejected
    if u['driver_status'] == "rejected":
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📨 Qayta ariza yuborish", callback_data="apply_driver")
        )
        return await message.answer(
            "❌ Ariza rad etilgan",
            reply_markup=kb
        )

    # ✅ APPROVED
    await message.answer(
        "🚘 Haydovchi bo‘limi:",
        reply_markup=driver_main_inline()
    )

# ---------------- YOLOVCHI SECTION ----------------
@dp.message_handler(lambda m: m.text == "🧍 Yo‘lovchi")
async def passenger_section(message: types.Message):
    uid = str(message.from_user.id)
    if uid not in data['users']:
        data['users'][uid] = {
            "role": None,
            "driver_status": "none",
            "driver_paused": False,
            "state": None,
            "driver_temp": {},
            "pass_temp": {},
            "full_name": message.from_user.full_name or "",
            "username": message.from_user.username or ""
        }
        save_json(DATA_FILE, data)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 E’lon berish", "◀️ Orqaga")
    await message.answer("Yo‘lovchi bo‘limi:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "📝 E’lon berish")
async def pass_ad_start(message: types.Message):
    uid = str(message.from_user.id)

    data['users'][uid]['state'] = "pass_text"
    save_json(DATA_FILE, data)

    await message.answer("✍️ E’lon matnini yozing:")

# ---------------- HAYDOVCHI ARIZA ----------------
@dp.message_handler(lambda m: m.text == "📨 Haydovchi bo‘lish uchun ariza yuborish")
async def driver_apply(message: types.Message):
    uid = str(message.from_user.id)
    u = data['users'].get(uid)
    # Allow re-application if previously rejected or none. Block only if pending or already approved.
    if u and u.get('driver_status') == "pending":
        return await message.answer("Siz allaqachon ariza yuborgansiz. Iltimos kuting.", reply_markup=back_btn())
    if u and u.get('driver_status') == "approved":
        return await message.answer("Siz allaqachon tasdiqlangan haydovchisiz.", reply_markup=driver_main_kb())

    # Ensure user record exists and update display info
    if uid not in data['users']:
        data['users'][uid] = {
            "role": None,
            "driver_status": "none",
            "driver_paused": False,
            "state": None,
            "driver_temp": {},
            "pass_temp": {},
            "full_name": message.from_user.full_name or "",
            "username": message.from_user.username or ""
        }

    # mark as pending
    data['users'][uid]['driver_status'] = "pending"
    data['users'][uid]['driver_paused'] = False
    # Save display info in user root so admin list can always use it
    data['users'][uid]['full_name'] = message.from_user.full_name or data['users'][uid].get('full_name', '')
    data['users'][uid]['username'] = message.from_user.username or data['users'][uid].get('username', '')
    # also keep a snapshot in driver_temp for later detailed info if needed
    data['users'][uid].setdefault('driver_temp', {})
    data['users'][uid]['driver_temp']['name'] = data['users'][uid]['full_name'] or data['users'][uid]['username'] or f"ID:{uid}"

    # Before sending new admin notifications, clear old admin_notifs for this uid
    data['admin_notifs'][uid] = []

    save_json(DATA_FILE, data)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"drv_ok:{uid}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"drv_no:{uid}")
    )

    for admin in ADMINS:
        try:
            username = message.from_user.username
            if username:
                username_display = f"@{username}"
            else:
                username_display = "—"
            msg = await bot.send_message(
                admin,
                f"🚘 Haydovchilik uchun ariza:\n👤 <b>{message.from_user.full_name}</b> ({username_display})\n🆔 <code>{uid}</code>",
                reply_markup=kb
            )
            # saqlaymiz: admin va message_id
            data['admin_notifs'].setdefault(uid, [])
            data['admin_notifs'][uid].append({"admin": admin, "msg_id": msg.message_id})
        except:
            pass
    save_json(DATA_FILE, data)
    await message.answer("Arizangiz adminga yuborildi! ⏳ Kuting.", reply_markup=back_btn())

# ---------------- ADMIN HAYDOVCHI TASDIQLASH ----------------
@dp.callback_query_handler(lambda c: c.data and (c.data.startswith("drv_ok:") or c.data.startswith("drv_no:") or c.data.startswith("drv_view:") or c.data.startswith("drv_remove:") or c.data.startswith("drv_keep:")))
async def admin_driver_action(call: types.CallbackQuery):
    # umumiy callback handling
    data_parts = call.data.split(":")
    action = data_parts[0]
    uid = data_parts[1] if len(data_parts) > 1 else None

    # faqat adminlar
    if int(call.from_user.id) not in ADMINS:
        await call.answer("Faqat adminlar uchun.", show_alert=True)
        return

    if action == "drv_ok":
        # tasdiqlash
        if uid not in data['users']:
            await call.answer("Foydalanuvchi topilmadi.")
            return
        data['users'][uid]['driver_status'] = "approved"
        data['users'][uid]['driver_paused'] = False
        save_json(DATA_FILE, data)

        # update: barcha adminlarga yuborilgan xabarlarni yangilash
        notifs = data.get('admin_notifs', {}).get(uid, [])
        for item in notifs:
            try:
                await bot.edit_message_text("✅ Amal bajarildi (tasdiqlandi)", item['admin'], item['msg_id'])
            except:
                pass

        # foydalanuvchiga xabar
        try:
            await bot.send_message(uid, "🎉 Admin sizni tasdiqladi! Endi haydovchi bo‘limiga kira olasiz.", reply_markup=driver_main_kb())
        except:
            pass

        # darhol bir marotaba har bir e'lonni kanallarga yuborish (faollashtirilgan e'lonlar uchun)
        # (eski ishlashni saqlab qolyapmiz)
        for ad_id, ad in list(ads['driver'].items()):
            if ad.get('user') == uid and ad.get('active', False):
                for ch in DRIVER_CHANNELS:
                    try:
                        kb = InlineKeyboardMarkup()
                        bot_username_for_url = BOT_USERNAME.lstrip('@')
                        kb.add(InlineKeyboardButton("📩 Zakaz berish", url=f"https://t.me/{bot_username_for_url}?start=zakaz"))
                        if ad.get('photo'):
                            await bot.send_photo(ch, ad['photo'], caption=ad.get('text', ''), reply_markup=kb)
                        else:
                            await bot.send_message(ch, ad.get('text', ''), reply_markup=kb)
                        ad['last_sent'] = time.time()
                    except:
                        pass
        save_json(ADS_FILE, ads)
        save_json(DATA_FILE, data)

    elif action == "drv_no":
        # rad etish
        if uid not in data['users']:
            await call.answer("Foydalanuvchi topilmadi.")
            return
        data['users'][uid]['driver_status'] = "rejected"
        data['users'][uid]['driver_paused'] = False
        save_json(DATA_FILE, data)

        # update admin notifs
        notifs = data.get('admin_notifs', {}).get(uid, [])
        for item in notifs:
            try:
                await bot.edit_message_text("❌ Amal bajarildi (rad etildi)", item['admin'], item['msg_id'])
            except:
                pass

        try:
            await bot.send_message(uid, "❌ Admin arizani rad etdi. Agar xohlasangiz qayta ariza yuborishingiz mumkin.", reply_markup=main_menu())
        except:
            pass

    elif action == "drv_view":
        # Admin haydovchilar ro'yxatidan -> bitta haydovchini ko'rish
        if uid not in data['users']:
            await call.answer("Foydalanuvchi topilmadi.")
            return
        u = data['users'][uid]
        # Topilgan haydovchining ma'lumotlari
        display_name = u.get('full_name') or u.get('driver_temp', {}).get('name') or (("@" + u['username']) if u.get('username') else f"ID:{uid}")
        txt = (
            f"🚘 <b>Haydovchi ma'lumotlari:</b>\n\n"
            f"👤 <b>Ism:</b> {display_name}\n"
            f"🆔 <code>{uid}</code>\n\n"
            f"📋 <i>Status:</i> {u.get('driver_status', '—')}\n"
        )
        # Tugmalar: chiqarib tashlash va qoldirish
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("❌ Chiqarib tashlash", callback_data=f"drv_remove:{uid}"),
            InlineKeyboardButton("✅ Qoldirish", callback_data=f"drv_keep:{uid}")
        )
        # Javobni adminga yuboramiz (call.message ga edit emas, yangi xabar)
        try:
            await bot.send_message(call.from_user.id, txt, reply_markup=kb, parse_mode="HTML")
        except:
            pass

    elif action == "drv_remove":
        # admin tomonidan chiqarib tashlash (haydovchilik huquqini olib tashlash)
        if uid not in data['users']:
            await call.answer("Foydalanuvchi topilmadi.")
            return
        data['users'][uid]['driver_status'] = "rejected"
        data['users'][uid]['driver_paused'] = False
        save_json(DATA_FILE, data)
        await call.answer("Foydalanuvchi chiqarib tashlandi.")
        try:
            await bot.send_message(uid, "❌ Siz haydovchi sifatida chiqarib tashlandingiz.", reply_markup=main_menu())
        except:
            pass

    elif action == "drv_keep":
        # admin tomonidan saqlash (hech narsa o'zgarmaydi, lekin xabar beramiz)
        if uid not in data['users']:
            await call.answer("Foydalanuvchi topilmadi.")
            return
        data['users'][uid]['driver_status'] = "approved"
        save_json(DATA_FILE, data)
        await call.answer("Foydalanuvchi haydovchi sifatida qoldirildi.")
        try:
            await bot.send_message(uid, "✅ Siz haydovchi sifatida qoldirildingiz.", reply_markup=driver_main_kb())
        except:
            pass

    # tugmani bosgan admin xabarini tahrirlash (mahalliy)
    try:
        await call.message.edit_text("✅ Amal bajarildi")
    except:
        pass
    await call.answer()

# ---------------- HAYDOVCHI E’LON BERISH ----------------
# --- DRIVER NEW FLOW ---

@dp.message_handler(lambda m: m.text == "📣 E’lon berish")
async def driver_new_ad(message: types.Message):
    uid = str(message.from_user.id)
    data['users'][uid]['state'] = "driver_text"
    save_json(DATA_FILE, data)
    await message.answer("✍️ E’lon matnini yuboring:")


@dp.message_handler(lambda m: data['users'].get(str(m.from_user.id), {}).get('state') == "driver_text")
async def driver_text(message: types.Message):
    uid = str(message.from_user.id)
    data['users'][uid]['driver_temp'] = {"text": message.text}
    data['users'][uid]['state'] = "driver_photo"
    save_json(DATA_FILE, data)

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⏭ O‘tkazib yuborish", callback_data="skip_photo")
    )

    await message.answer("📸 Mashina rasmini yuboring (majburiy emas)", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == "skip_photo")
async def skip_photo(call: types.CallbackQuery):
    uid = str(call.from_user.id)

    data['users'][uid]['state'] = "driver_interval"
    save_json(DATA_FILE, data)

    kb = InlineKeyboardMarkup(row_width=2)
    for i in [5,10,15,20,30]:
        kb.insert(InlineKeyboardButton(f"{i} min", callback_data=f"interval:{i}"))

    await call.message.answer("⏱ Necha minutda yuborilsin?", reply_markup=kb)


@dp.message_handler(content_types=['photo'])
async def get_photo(message: types.Message):
    uid = str(message.from_user.id)

    if data['users'][uid]['state'] != "driver_photo":
        return

    data['users'][uid]['driver_temp']['photo'] = message.photo[-1].file_id
    data['users'][uid]['state'] = "driver_interval"
    save_json(DATA_FILE, data)

    kb = InlineKeyboardMarkup(row_width=2)
    for i in [5,10,15,20,30]:
        kb.insert(InlineKeyboardButton(f"{i} min", callback_data=f"interval:{i}"))

    await message.answer("⏱ Necha minutda yuborilsin?", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("interval:"))
async def set_interval(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    interval = int(call.data.split(":")[1])

    data['users'][uid]['driver_temp']['interval'] = interval
    data['users'][uid]['state'] = "driver_confirm"
    save_json(DATA_FILE, data)

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_ad"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_ad")
    )

    await call.message.answer("Tasdiqlaysizmi?", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == "confirm_ad")
async def confirm_ad(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    u = data['users'][uid]['driver_temp']

    ad_id = str(time.time()).replace('.', '')
    ads['driver'][ad_id] = {
        "user": uid,
        "text": u.get('text'),
        "photo": u.get('photo'),
        "interval": u.get('interval'),
        "start": time.time(),
        "active": True,
        "last_sent": 0
    }

    save_json(ADS_FILE, ads)

    data['users'][uid]['state'] = None
    data['users'][uid]['driver_temp'] = {}
    save_json(DATA_FILE, data)

    await call.message.answer("🚀 E’lon ishga tushdi!")

# ---------------- DRIVER LOOP ----------------
async def driver_loop():
    """
    Har bir ad uchun last_sent soatiga qarab yuborishni boshqaradi.
    Bu usul tufayli bir ad yuborilgach, boshqa adlar bloklanib qolmaydi.
    Qo'shimcha: foydalanuvchi pauza qilgan bo'lsa (driver_paused) ad yuborilmaydi darhol.
    """
    while True:
        now = time.time()
        changed = False
        for ad_id, ad in list(ads['driver'].items()):
            try:
                if not ad.get('active', False):
                    continue
                # agar e'lon 1 kundan ortiq bo'lsa uni avtomatik oʻchir
                if now - ad.get('start', now) > 86400:
                    ads['driver'][ad_id]['active'] = False
                    changed = True
                    continue

                # agar foydalanuvchi pauza holatida bo'lsa — yubormaymiz
                user_uid = ad.get('user')
                if user_uid and data['users'].get(user_uid, {}).get('driver_paused', False):
                    continue

                interval_seconds = ad.get('interval', 1) * 60
                last = ad.get('last_sent', 0)
                # agar hech qachon yuborilmagan yoki interval o'tgan bo'lsa — yuborish
                if last == 0 or (now - last) >= interval_seconds:
                    for ch in DRIVER_CHANNELS:
                        try:
                            kb = InlineKeyboardMarkup()
                            bot_username_for_url = BOT_USERNAME.lstrip('@')
                            kb.add(InlineKeyboardButton("📩 Zakaz berish", url=f"https://t.me/{bot_username_for_url}?start=zakaz"))
                            if ad.get('photo'):
                                await bot.send_photo(ch, ad['photo'], caption=ad.get('text', ''), reply_markup=kb)
                            else:
                                await bot.send_message(ch, ad.get('text', ''), reply_markup=kb)
                            # belgila yuborilgan vaqtni
                            ads['driver'][ad_id]['last_sent'] = time.time()
                            changed = True
                        except:
                            pass
                    # kichik kutish — keyingi adga o'tish uchun
                    await asyncio.sleep(0.5)
            except:
                pass
        if changed:
            save_json(ADS_FILE, ads)
        await asyncio.sleep(2)

# ---------------- PAUSE / NEW AD ----------------
@dp.message_handler(lambda m: m.text == "⏸ To‘xtatish")
async def pause_driver(message: types.Message):
    uid = str(message.from_user.id)
    any_changed = False

    # 1) Mark user as paused in data (immediate effect in loop)
    if uid in data['users']:
        data['users'][uid]['driver_paused'] = True
        save_json(DATA_FILE, data)

    # 2) Also mark any active ads of this user as inactive (defensive)
    for ad in ads['driver'].values():
        if ad.get('user') == uid and ad.get('active', False):
            ad['active'] = False
            any_changed = True
    if any_changed:
        save_json(ADS_FILE, ads)

    await message.answer("⏸ Pauza qilindi.", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "🆕 Yangi e’lon")
async def new_driver_ad(message: types.Message):
    # yangi e'lon bosilganda pauzani avtomatik o'chirish (foydalanuvchi e'lonni yana boshlamoqchi)
    uid = str(message.from_user.id)
    if uid in data['users']:
        data['users'][uid]['driver_paused'] = False
        save_json(DATA_FILE, data)
    return await driver_new_ad(message)

import re

@dp.callback_query_handler(lambda c: c.data == "pass_ad")
async def pass_ad(call: types.CallbackQuery):
    uid = str(call.from_user.id)

    if uid not in data['users']:
        data['users'][uid] = {}

    data['users'][uid]['state'] = "pass_text"
    save_json(DATA_FILE, data)

    await call.message.answer("✍️ E’loningizni yuboring:")


@dp.message_handler(lambda m: data['users'].get(str(m.from_user.id), {}).get('state') == "pass_text")
async def pass_text(message: types.Message):
    uid = str(message.from_user.id)

    text = message.text
    phone = re.findall(r"\+?\d{9,13}", text)

    if phone:
        await send_passenger_ad(uid, text, phone[0])
    else:
        data['users'][uid]['pass_temp'] = {"text": text}
        data['users'][uid]['state'] = "pass_phone"
        save_json(DATA_FILE, data)
        await message.answer("📞 Telefon raqam yuboring:")


@dp.message_handler(lambda m: data['users'].get(str(m.from_user.id), {}).get('state') == "pass_phone")
async def pass_phone(message: types.Message):
    uid = str(message.from_user.id)

    text = data['users'][uid]['pass_temp']['text']
    phone = message.text

    await send_passenger_ad(uid, text, phone)


async def send_passenger_ad(uid, text, phone):
    ad_id = str(time.time())

    ads['passenger'][ad_id] = {
        "user": uid,
        "text": text,
        "phone": phone,
        "taken_by": None
    }

    save_json(ADS_FILE, ads)

    await bot.send_message(uid,
        "✅ Eloningiz shofyorlarga yuborildi.\n"
        "Iltimos boshqa guruhlarga yubormang.\n\n"
        "🚖 COMFORT taxi - eng yaxshi tanlov"
    )

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📩 Ko‘rish", callback_data=f"view_pass:{ad_id}")
    )

    for ch in PASSENGER_CHANNELS:
        await bot.send_message(ch, text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("take_pass:"))
async def take_pass(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    ad_id = call.data.split(":")[1]
    ad = ads['passenger'].get(ad_id)
    if not ad:
        return await call.answer("Topilmadi", show_alert=True)

    if ad.get('taken_by'):
        return await call.answer("❌ Boshqa foydalanuvchi allaqachon qabul qilgan.", show_alert=True)

    # Shu foydalanuvchi qabul qildi
    ad['taken_by'] = uid
    save_json(ADS_FILE, ads)

    # Guruhdagi eslatma tugmasini o'zgartirish
    for ch in PASSENGER_CHANNELS:
        try:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Qabul qilindi", callback_data="none"))
            await bot.edit_message_reply_markup(chat_id=ch, message_id=ad.get('group_msg_id'), reply_markup=kb)
        except:
            pass

    await call.message.edit_reply_markup(reply_markup=None)  # o'zida tugmani olib tashlaymiz
    await call.message.answer("✅ Siz e’lonni qabul qildingiz.")


# ---------------- YOLOVCHI CALLBACKS ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("view_pass:"))
async def view_passenger(call: types.CallbackQuery):
    ad_id = call.data.split(":")[1]
    ad = ads['passenger'].get(ad_id)
    if not ad:
        return await call.answer("Topilmadi", show_alert=True)

    # Agar e'lon boshqa foydalanuvchi tomonidan qabul qilingan bo'lsa
    if ad.get('taken_by'):
        return await call.answer("❌ Ushbu e'lon allaqachon qabul qilingan.", show_alert=True)

    # Botga shaxsiy chatda faqat shu foydalanuvchi uchun
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Qabul qilish", callback_data=f"take_pass:{ad_id}"))

    await call.from_user.send_message(ad['text'], reply_markup=kb)
    await call.answer("E’lon botga ochildi ✅", show_alert=True)

# --- Qabul qilish tugmasi ---
@dp.callback_query_handler(lambda c: c.data.startswith("take_pass:"))
async def take_passenger(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    ad_id = call.data.split(":")[1]
    ad = ads['passenger'].get(ad_id)
    if not ad:
        return await call.answer("Topilmadi", show_alert=True)

    if ad.get('taken_by'):
        return await call.answer("❌ Boshqa foydalanuvchi allaqachon qabul qilgan.", show_alert=True)

    # Shu foydalanuvchi qabul qildi
    ad['taken_by'] = uid
    save_json(ADS_FILE, ads)

    # Guruhdagi eslatmani "Qabul qilindi" ga o'zgartirish
    for ch in PASSENGER_CHANNELS:
        try:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Qabul qilindi", callback_data="none"))
            await bot.edit_message_reply_markup(chat_id=ch, message_id=ad.get('group_msg_id'), reply_markup=kb)
        except:
            pass

    # Faqat shu foydalanuvchiga xabar
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("✅ Siz e’lonni qabul qildingiz.")

@dp.message_handler(lambda m: m.text == "📥 Yo‘lovchi e’lonlari")
async def passenger_ads_menu(message: types.Message):
    uid = str(message.from_user.id)
    if data['users'].get(uid, {}).get('driver_status') != "approved" and int(uid) not in ADMINS:
        return await message.answer("❌ Sizga ruxsat yo‘q")

    kb = InlineKeyboardMarkup()
    for ad_id, ad in ads.get('passenger', {}).items():
        # faqat faol e'lonlar (24 soat ichida)
        if time.time() - ad['created'] > 86400:
            continue
        kb.add(InlineKeyboardButton("📥 Ko‘rish", callback_data=f"view_pass:{ad_id}"))

    if not kb.inline_keyboard:
        await message.answer("❌ Faol yo‘lovchi e’lonlari yo‘q.")
    else:
        await message.answer("📥 Yo‘lovchi e’lonlari:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("view_pass:"))
async def view_pass(call: types.CallbackQuery):
    ad_id = call.data.split(":")[1]
    ad = ads['passenger'].get(ad_id)
    if not ad:
        await call.answer("E’lon topilmadi", show_alert=True)
        return

    # Agar e’lon allaqachon boshqa haydovchi tomonidan olingan bo‘lsa
    if ad.get('taken_by') and ad['taken_by'] != str(call.from_user.id):
        await call.answer("❌ Bu e’lon boshqa haydovchi tomonidan olingan.", show_alert=True)
        return

    # E’lonni hozirgi haydovchiga ko‘rsatish
    text = (
        f"🚖 Yo‘lovchi e’loni:\n\n"
        f"📍 Yo‘nalish: {ad['route']}\n"
        f"👥 Odamlar soni: {ad['people']}\n"
        f"🕒 Vaqt: {ad['time']}\n"
        f"📞 Telefon: {ad['phone']}\n"
    )
    await bot.send_message(call.from_user.id, text)

    # E’lonni shu foydalanuvchi olgan deb belgilaymiz
    ad['taken_by'] = str(call.from_user.id)
    save_json(ADS_FILE, ads)

    await call.answer("✅ E’lon sizga berildi", show_alert=True)

@dp.message_handler(lambda m: m.text == "📥 Yo‘lovchi e’lonlari")
async def my_passenger_ads(message: types.Message):
    uid = str(message.from_user.id)
    text = "📥 Yo‘lovchi e’lonlari:\n\n"
    for ad_id, ad in ads['passenger'].items():
        if ad.get('taken_by') is None:  # hali hech kim olmagan e’lonlar
            text += f"• {ad['route']} - {ad['people']} kishi\n"
    if text == "📥 Yo‘lovchi e’lonlari:\n\n":
        text = "Yo‘lovchi e’lonlari yo‘q."
    await message.answer(text)


#------------ UNIVERSAL "ORQAGA" HANDLER -
@dp.message_handler(lambda m: m.text == "◀️ Orqaga")
async def go_back(message: types.Message):
    uid = str(message.from_user.id)
    # reset any temporary state
    if uid in data['users']:
        data['users'][uid]['state'] = None
        data['users'][uid]['driver_temp'] = {}
        data['users'][uid]['pass_temp'] = {}
        save_json(DATA_FILE, data)
    is_admin = int(message.from_user.id) in ADMINS
    await message.answer("Asosiy menyuga qaytdingiz:", reply_markup=main_menu(is_admin=is_admin))

# ---------------- ADMINS: HAYDOVCHILAR RO'YXATI ----------------
@dp.message_handler(lambda m: m.text == "👥 Haydovchilar")
async def admin_drivers_list(message: types.Message):
    if int(message.from_user.id) not in ADMINS:
        return await message.answer("Faqat adminlar uchun.")

    inline = InlineKeyboardMarkup()
    found = False

    for uid, u in data['users'].items():
        if u.get('driver_status') == "approved":
            name = u.get('full_name') or u.get('username') or f"ID:{uid}"
            inline.add(InlineKeyboardButton(name, callback_data=f"drv_view:{uid}"))
            found = True

    if not found:
        return await message.answer("❌ Haydovchilar topilmadi.")

    await message.answer("🚘 Tasdiqlangan haydovchilar:", reply_markup=inline)

# ---------------- START BOT ----------------
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(driver_loop())
    executor.start_polling(dp, skip_updates=True)