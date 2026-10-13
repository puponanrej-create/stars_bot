import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile
)

API_TOKEN = '8211870455:AAGa_p1hwXYCNXZWjl518fwNdll_QxnHVLw'
ADMIN_ID = 8596393850
REQUISITES = "89878343491 (Альфа Банк)"
STARS_RATE = 1.44
STEAM_COMMISSION = 1.05

# Имена файлов медиа, которые должны лежать рядом с main.py
START_VIDEO = "start_video.mp4"
STARS_IMAGE = "stars_image.jpg"
STEAM_IMAGE = "https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?q=80&w=1000&auto=format&fit=crop"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Order(StatesGroup):
    steam_data = State()
    stars_count = State()
    stars_recipient = State()
    waiting_payment = State()

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎮 Пополнить Steam"), KeyboardButton(text="🌟 Купить Telegram Stars")],
        [KeyboardButton(text="💬 Поддержка")]
    ], resize_keyboard=True)

def stars_count_kb():
    buttons = [
        [InlineKeyboardButton(text="50 ⭐", callback_data="stars_50"), InlineKeyboardButton(text="100 ⭐", callback_data="stars_100")],
        [InlineKeyboardButton(text="500 ⭐", callback_data="stars_500"), InlineKeyboardButton(text="1000 ⭐", callback_data="stars_1000")],
        [InlineKeyboardButton(text="✏️ Своё кол-во", callback_data="stars_custom")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    caption = (
        "Добро пожаловать в автоматический сервис!\n\n"
        "⚡️ Здесь вы можете мгновенно и безопасно:\n"
        "• Пополнить баланс Steam 🎮\n"
        "• Купить Telegram Stars ⭐\n\n"
        "Выберите нужную услугу в меню ниже 👇"
    )
    video = FSInputFile(START_VIDEO)
    await message.answer_video(
        video=video,
        caption=caption,
        reply_markup=main_kb()
    )

@dp.message(F.text == "💬 Поддержка")
async def support(message: types.Message):
    await message.answer("По всем вопросам обращайтесь к администратору: @твой_юз")

# --- СТИМ ---
@dp.message(F.text == "🎮 Пополнить Steam")
async def steam_start(message: types.Message, state: FSMContext):
    text = (
        "🎮 **Пополнение Steam**\n\n"
        "Введите ваш **Логин Steam** (не ник) и **сумму пополнения** через пробел.\n"
        "Пример: `ivan_steam 500`"
    )
    await message.answer_photo(photo=STEAM_IMAGE, caption=text)
    await state.set_state(Order.steam_data)

@dp.message(Order.steam_data)
async def steam_process(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        login = parts[0]
        amount = float(parts[1])
        total = amount * STEAM_COMMISSION
        
        await state.update_data(service="Steam", login=login, amount=amount, total=total)
        
        text = (
            f"🎮 **Заказ Steam**\n"
            f"Логин: `{login}`\n"
            f"Сумма пополнения: {amount} руб.\n\n"
            f"💳 **К оплате (с учетом комиссии):** `{total:.2f}` руб.\n\n"
            f"🏦 **Реквизиты для оплаты:**\n"
            f"`{REQUISITES}`\n\n"
            f"⚠️ После оплаты обязательно отправьте **скриншот чека** (фото или документ) в этот чат!"
        )
        await message.answer(text)
        await state.set_state(Order.waiting_payment)
    except:
        await message.answer("❌ Ошибка в формате! Введите логин и сумму через пробел (например: `my_login 300`).")

# --- ЗВЕЗДЫ ---
@dp.message(F.text == "🌟 Купить Telegram Stars")
async def stars_start(message: types.Message):
    text = "🌟 **Покупка Telegram Stars**\n\nВыберите количество звезд из списка ниже или укажите свое:"
    photo = FSInputFile(STARS_IMAGE)
    await message.answer_photo(photo=photo, caption=text, reply_markup=stars_count_kb())

@dp.callback_query(F.data.startswith("stars_"))
async def stars_select(callback: types.CallbackQuery, state: FSMContext):
    count_data = callback.data.split("_")[1]
    if count_data == "custom":
        await callback.message.answer("✏️ Введите желаемое количество звезд (минимум 50):")
        await state.set_state(Order.stars_count)
    else:
        count = int(count_data)
        await state.update_data(stars_count=count)
        await ask_stars_recipient(callback.message, state)
    await callback.answer()

@dp.message(Order.stars_count)
async def stars_custom_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 50:
            await message.answer("Минимальное количество звезд — 50. Введите снова:")
            return
        await state.update_data(stars_count=count)
        await ask_stars_recipient(message, state)
    except:
        await message.answer("Введите число (например: 150):")

async def ask_stars_recipient(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Себе", callback_data="target_me")],
        [InlineKeyboardButton(text="👥 Другому юзеру", callback_data="target_other")]
    ])
    await message.answer("Куда отправить звезды?", reply_markup=kb)

@dp.callback_query(F.data.startswith("target_"))
async def stars_target(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "target_me":
        data = await state.get_data()
        total = data['stars_count'] * STARS_RATE
        username = f"@{callback.from_user.username}" if callback.from_user.username else f"ID:{callback.from_user.id}"
        await state.update_data(recipient=username, total=total, service="Stars")
        await finalize_stars_order(callback.message, state)
    else:
        await callback.message.answer("✏️ Введите `@username` получателя звезд:")
        await state.set_state(Order.stars_recipient)
    await callback.answer()

@dp.message(Order.stars_recipient)
async def stars_custom_recipient(message: types.Message, state: FSMContext):
    data = await state.get_data()
    total = data['stars_count'] * STARS_RATE
    await state.update_data(recipient=message.text, total=total, service="Stars")
    await finalize_stars_order(message, state)

async def finalize_stars_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = (
        f"🌟 **Заказ Telegram Stars**\n"
        f"Количество: {data['stars_count']} ⭐\n"
        f"Получатель: {data['recipient']}\n\n"
        f"💳 **К оплате:** `{data['total']:.2f}` руб.\n\n"
        f"🏦 **Реквизиты для оплаты:**\n"
        f"`{REQUISITES}`\n\n"
        f"⚠️ После оплаты обязательно отправьте **скриншот чека** в этот чат!"
    )
    await message.answer(text)
    await state.set_state(Order.waiting_payment)

# --- ПРИЕМ ЧЕКА ---
@dp.message(Order.waiting_payment, F.photo | F.document)
async def handle_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    admin_msg = (
        f"📦 **НОВЫЙ ЗАКАЗ НА ПРОВЕРКУ**\n"
        f"👤 От: @{message.from_user.username or 'нет юза'} (ID: `{message.from_user.id}`)\n"
        f"🛠 Услуга: {data['service']}\n"
        f"📌 Данные: `{data.get('login') or data.get('recipient')}`\n"
        f"💰 Сумма: `{data['total']:.2f}` руб."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправил / Выполнено", callback_data=f"done_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cancel_{message.from_user.id}")]
    ])
    
    await bot.send_message(ADMIN_ID, admin_msg)
    
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, reply_markup=kb)
    else:
        await bot.send_document(ADMIN_ID, message.document.file_id, reply_markup=kb)
        
    await message.answer("⏳ Чек принят и отправлен администратору. Ожидайте зачисления!")
    await state.clear()

# --- КНОПКИ АДМИНА ---
@dp.callback_query(F.data.startswith("done_"))
async def admin_done(callback: types.CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(user_id, "🎉 Ваш заказ успешно выполнен! Спасибо, что выбрали нас ❤️")
    await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n🟢 СТАТУС: ВЫПОЛНЕНО")
    await callback.answer("Заказ отмечен как выполненный!")

@dp.callback_query(F.data.startswith("cancel_"))
async def admin_cancel(callback: types.CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(user_id, "❌ Ваш заказ был отклонен. Если это ошибка, напишите в поддержку.")
    await callback.message.edit_caption(caption=(callback.message.caption or "") + "\n\n🔴 СТАТУС: ОТКЛОНЕНО")
    await callback.answer("Заказ отклонен")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
