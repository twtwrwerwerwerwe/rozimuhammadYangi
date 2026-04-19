# taxi_bot_final_fixed.py
import asyncio
import json
import time
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ---------------- CONFIG ----------------
TOKEN = "8474009974:AAERXCF7Jj1Qv-QGixFGaFVIgnUZcoIJoPs"
ADMINS = [6302873072]
BOT_USERNAME = "@rishtonBogdodToshkentTaxi_bot"

# Bu yerga 1 yoki undan ortiq kanal id larini qo'yishingiz mumkin.
DRIVER_CHANNELS = [-1003322681147]

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
# ---------------- INIT FILES ----------------
if not DATA_FILE.exists():
    save_json(DATA_FILE, {"users": {}, "admin_notifs": {}})

if not ADS_FILE.exists():
    save_json(ADS_FILE, {"driver": {}})

# ---------------- LOAD DATA ----------------
data = load_json(DATA_FILE, {"users": {}, "admin_notifs": {}})
ads = load_json(ADS_FILE, {"driver": {}})

# ---------------- BOT ----------------
bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

data = load_json(DATA_FILE, {"users":{}, "admin_notifs": {}})

# ---------------- KEYBOARDS ----------------
def main_menu(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # HAMMA UCHUN
    kb.add(KeyboardButton("🚘 Haydovchi"))
    
    # FAQAT ADMIN
    if is_admin:
        kb.add(KeyboardButton("👥 Haydovchilar"))
        
    return kb

def back_btn():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("◀️ Orqaga")
    return kb

def driver_main_kb():
    # after approval show minimal options (no "Davom etish")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📣 E’lon berish", "⏸ To‘xtatish")
    kb.add("🆕 Yangi e’lon", "◀️ Orqaga")
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
            "phone": None,
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

# ---------------- HAYDOVCHI SECTION ----------------
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

# ---------------- CALLBACKS ----------------
driver_cb = CallbackData("driver", "action", "uid")

# ---------------- TO'LOV TUGMASI ----------------
def payment_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            text="💳 To‘lov qilish",
            url="https://t.me/akramjonov777"  # admin profili
        )
    )
    return kb

# ---------------- HAYDOVCHI BO‘LIM ----------------
@dp.message_handler(lambda m: m.text == "🚘 Haydovchi")
async def driver_section(message: types.Message):
    uid = str(message.from_user.id)

    # Foydalanuvchi yo‘q bo‘lsa yaratish
    if uid not in data['users']:
        data['users'][uid] = {
            "role": None,
            "driver_status": "none",  # none, pending, approved, rejected
            "driver_paused": False,
            "state": None,
            "driver_temp": {},
            "pass_temp": {},
            "full_name": message.from_user.full_name or "",
            "username": message.from_user.username or ""
        }
        save_json(DATA_FILE, data)

    u = data['users'][uid]

    # Admin bo‘lsa
    if int(uid) in ADMINS:
        data['users'][uid]['driver_status'] = "approved"
        data['users'][uid]['driver_paused'] = False
        save_json(DATA_FILE, data)
        return await message.answer(
            "Haydovchi bo‘limi (admin):",
            reply_markup=driver_main_kb()
        )

    # Tasdiqlangan haydovchi
    if u.get("driver_status") == "approved":
    
    # agar telefon yo‘q bo‘lsa — majburiy so‘raymiz
        if not u.get("phone"):
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton("📞 Raqamni yuborish", request_contact=True))
            
            data['users'][uid]['state'] = "get_phone"
            save_json(DATA_FILE, data)

            return await message.answer(
                "📞 Iltimos telefon raqamingizni yuboring:",
                reply_markup=kb
            )

        return await message.answer(
            "Haydovchi bo‘limi:",
            reply_markup=driver_main_kb()
        )

    # Hali haydovchi bo‘lmagan foydalanuvchi
    text = (
        "🚘 <b>Haydovchi bo‘limi</b>\n\n"
        "Bu bo‘limdan foydalanish uchun <b>to‘lov qilishingiz kerak</b> 💰\n\n"
        "👇 Pastdagi tugma orqali admin bilan bog‘lanib to‘lovni amalga oshiring.\n"
        "To‘lovdan so‘ng <b>arizani yuborish</b> tugmasini bosing."
    )

    # ReplyKeyboard: Ariza yuborish + Orqaga
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📨 Ariza yuborish", "◀️ Orqaga")

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

    # InlineKeyboard: To‘lov qilish
    await message.answer(
        "💳 To‘lov qilish uchun admin bilan bog‘laning:",
        reply_markup=payment_kb()
    )

# ---------------- ARIZA YUBORISH ----------------
@dp.message_handler(lambda m: m.text == "📨 Ariza yuborish")
async def send_driver_request(message: types.Message):
    uid = str(message.from_user.id)
    u = data['users'][uid]

    # Rad etilgan bo‘lsa, yana yuborishga ruxsat
    if u.get("driver_status") == "rejected":
        u['driver_status'] = "none"
        save_json(DATA_FILE, data)

    u['driver_status'] = "pending"
    save_json(DATA_FILE, data)

    # Adminga ariza xabari
    admins_text = (
        f"🚨 <b>Yangi haydovchi arizasi</b>\n\n"
        f"Foydalanuvchi: {u.get('full_name')} (@{u.get('username')})\n"
        f"ID: {uid}\n"
        f"Niki: @{u.get('username')}\n\n"
        "To‘lov qilgan bo‘lsa, tasdiqlashni unutmang."
    )

    # InlineKeyboard: Tasdiqlash / Rad etish
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(
            text="✅ Tasdiqlash",
            callback_data=driver_cb.new(action="approve", uid=uid)
        ),
        InlineKeyboardButton(
            text="❌ Rad etish",
            callback_data=driver_cb.new(action="reject", uid=uid)
        )
    )

    for admin_id in ADMINS:
        await bot.send_message(admin_id, admins_text, parse_mode="HTML", reply_markup=kb)

    # Foydalanuvchiga xabar
    await message.answer(
        "✅ Arizangiz adminga yuborildi.\n"
        "To‘lov qilganingizni tasdiqlangandan so‘ng siz haydovchi sifatida tasdiqlanasiz.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("◀️ Orqaga")
    )

# ---------------- CALLBACK HANDLER ----------------
@dp.callback_query_handler(driver_cb.filter())
async def driver_callback_handler(query: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    uid = callback_data['uid']

    if uid not in data['users']:
        return await query.answer("Foydalanuvchi topilmadi.", show_alert=True)

    user = data['users'][uid]

    if action == "approve":
        user['driver_status'] = "approved"
        save_json(DATA_FILE, data)
        await query.message.edit_text(f"✅ {user.get('full_name')} haydovchi sifatida tasdiqlandi.")
        # Foydalanuvchiga xabar
        await bot.send_message(uid, "🎉 Siz haydovchi sifatida tasdiqlandingiz!", reply_markup=driver_main_kb())

    elif action == "reject":
        user['driver_status'] = "rejected"
        save_json(DATA_FILE, data)
        await query.message.edit_text(f"❌ {user.get('full_name')} rad etildi.")
        # Foydalanuvchiga xabar
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📨 Qayta yuborish", "◀️ Orqaga")
        await bot.send_message(
            uid,
            "❌ Siz rad etildingiz. Iltimos to‘lov qilib qayta urinib ko‘ring.",
            reply_markup=kb
        )

# ---------------- QAYTA YUBORISH ----------------
@dp.message_handler(lambda m: m.text == "📨 Qayta yuborish")
async def resend_driver_request(message: types.Message):
    await send_driver_request(message)


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

                        # 🔥 DRIVER TELEFONINI OLAMIZ
                        driver_uid = ad.get('user')
                        driver_phone = data['users'].get(driver_uid, {}).get('phone')

                        # 🔥 AGAR TELEFON BOR BO‘LSA
                        if driver_phone:
                            kb.add(
                                InlineKeyboardButton(
                                    "📞 Qo‘ng‘iroq qilish",
                                    url=f"tel:{driver_phone}"
                                )
                            )
                        else:
                            # fallback (agar raqam yo‘q bo‘lsa)
                            kb.add(
                                InlineKeyboardButton(
                                    "❌ Raqam mavjud emas",
                                    callback_data="no_phone"
                                )
                            )

                        # 🔥 E’LONNI YUBORISH
                        if ad.get('photo'):
                            await bot.send_photo(
                                ch,
                                ad['photo'],
                                caption=ad.get('text', ''),
                                reply_markup=kb
                            )
                        else:
                            await bot.send_message(
                                ch,
                                ad.get('text', ''),
                                reply_markup=kb
                            )

                        # 🔥 VAQTNI BELGILASH
                        ad['last_sent'] = time.time()

                    except Exception as e:
                        print("Xatolik:", e)

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
@dp.message_handler(lambda m: m.text == "📣 E’lon berish")
async def driver_new_ad(message: types.Message):
    uid = str(message.from_user.id)
    if data['users'].get(uid, {}).get('driver_status') != "approved":
        return await message.answer("❌ Siz hali haydovchi emassiz yoki admin arizani tasdiqlamagan.", reply_markup=back_btn())
    data['users'][uid]['state'] = "driver_text"
    data['users'][uid]['driver_temp'] = {}
    # e'lon yaratishda avtomatik pauza o'chirilgan bo'lsin
    data['users'][uid]['driver_paused'] = False
    save_json(DATA_FILE, data)
    await message.answer("✍️ E’lon matnini yuboring:", reply_markup=back_btn())

# ---------------- DRIVER HANDLERS ----------------
@dp.message_handler(lambda m: data['users'].get(str(m.from_user.id), {}).get('state') == "driver_text")
async def driver_get_text(message: types.Message):
    uid = str(message.from_user.id)
    data['users'][uid]['driver_temp']['text'] = message.text
    data['users'][uid]['state'] = "driver_photo"
    save_json(DATA_FILE, data)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⏭ O‘tkazib yuborish", "◀️ Orqaga")

    await message.answer("📸 Mashina rasmini yuboring (majburiy emas):", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "⏭ O‘tkazib yuborish")
async def skip_photo(message: types.Message):
    uid = str(message.from_user.id)

    if data['users'][uid].get('state') != "driver_photo":
        return

    # rasm yo‘q deb belgilaymiz
    data['users'][uid]['driver_temp']['photo'] = None
    data['users'][uid]['state'] = "driver_interval"
    save_json(DATA_FILE, data)

    await message.answer("⏱ Necha daqiqada qayta yuborilsin? (masalan: 1)", reply_markup=back_btn())

@dp.message_handler(content_types=['photo'])
async def driver_get_photo(message: types.Message):
    uid = str(message.from_user.id)
    if data['users'][uid].get('state') != "driver_photo":
        return
    file_id = message.photo[-1].file_id
    data['users'][uid]['driver_temp']['photo'] = file_id
    data['users'][uid]['state'] = "driver_interval"
    save_json(DATA_FILE, data)
    await message.answer("⏱ Necha daqiqada qayta yuborilsin? (masalan: 1)", reply_markup=back_btn())

@dp.message_handler(lambda m: data['users'].get(str(m.from_user.id), {}).get('state') == "driver_interval")
async def driver_get_interval(message: types.Message):
    uid = str(message.from_user.id)
    try:
        interval = int(message.text)
    except:
        return await message.answer("Faqat son kiriting!", reply_markup=back_btn())
    data['users'][uid]['driver_temp']['interval'] = interval
    data['users'][uid]['state'] = "driver_confirm"
    save_json(DATA_FILE, data)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    # Tasdiqlash/Tozalash va Orqaga — lekin "Davom etish" olib tashlandi
    kb.add("✅ Tasdiqlash", "🗑 Tozalash")
    kb.add("◀️ Orqaga")
    await message.answer("Hammasi tayyor. Tasdiqlaysizmi?", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "🗑 Tozalash")
async def driver_clear(message: types.Message):
    uid = str(message.from_user.id)
    data['users'][uid]['driver_temp'] = {}
    data['users'][uid]['state'] = None
    save_json(DATA_FILE, data)
    await message.answer("Tozalandi!", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "✅ Tasdiqlash")
async def driver_confirm(message: types.Message):
    uid = str(message.from_user.id)
    u = data['users'][uid]['driver_temp']
    # ad yaratish
    ad_id = str(time.time()).replace('.', '')
    ads['driver'][ad_id] = {
        "user": uid,
        "text": u.get('text', ''),
        "photo": u.get('photo'),
        # interval daqiqada
        "interval": max(0.1, u.get('interval', 1)),
        "start": time.time(),
        "active": True,
        "last_sent": 0
    }
    save_json(ADS_FILE, ads)

    data['users'][uid]['driver_temp'] = {}
    data['users'][uid]['state'] = None
    # e'lon yaratishda pauza false bo'lsin
    data['users'][uid]['driver_paused'] = False
    save_json(DATA_FILE, data)

    # xabar: e'lon yuborish boshlandi va minimal tugmalar (To'xtatish, Yangi e'lon, Orqaga)
    await message.answer("🚀 E’lon yuborish boshlandi!", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("⏸ To‘xtatish", "🆕 Yangi e’lon").add("◀️ Orqaga"))

@dp.message_handler(content_types=['contact'])
async def get_phone_handler(message: types.Message):
    uid = str(message.from_user.id)

    if data['users'][uid].get('state') != "get_phone":
        return

    phone = message.contact.phone_number

    data['users'][uid]['phone'] = phone
    data['users'][uid]['state'] = None
    save_json(DATA_FILE, data)

    await message.answer(
        "✅ Raqamingiz saqlandi!",
        reply_markup=driver_main_kb()
    )
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
                            kb.add(InlineKeyboardButton("📩 Zakaz berish", url=f"https://t.me/bagdod_rishton_taxi_bot?start=zakaz"))
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

# ---------------- UNIVERSAL "ORQAGA" HANDLER ----------------
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
    # barcha tasdiqlangan haydovchilarni topamiz
    inline = InlineKeyboardMarkup()
    found = False
    for uid, u in data['users'].items():
        if u.get('driver_status') == "approved":
            # display name logic: prefer stored full_name, then username, then driver_temp.name, then ID
            display = u.get('full_name') or (("@" + u['username']) if u.get('username') else u.get('driver_temp', {}).get('name') or f"ID:{uid}")
            inline.add(InlineKeyboardButton(display, callback_data=f"drv_view:{uid}"))
            found = True
    if not found:
        return await message.answer("Hozircha tasdiqlangan haydovchilar yo'q.")
    await message.answer("Tasdiqlangan haydovchilar:", reply_markup=None)
    await bot.send_message(message.from_user.id, "Ro'yxat:", reply_markup=inline)

# ---------------- START BOT ----------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(driver_loop())
    executor.start_polling(dp, skip_updates=True)
