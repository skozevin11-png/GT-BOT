import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Токен вашего бота от BotFather
TOKEN = "8798646610:AAEgHVTMQx0biu-85TYkF7Jyc3GFStCfWUk"

# API ключ из вашего запроса (используйте для запросов к внешней платежной системе/сервису)
API_KEY = "PRTNR-B3_AbtAsupKEnjKiS_4ZTzfZskIraDlUYy_wDS_CfO8"

router = Router()

# Временная база данных в памяти (для примера)
# В реальном проекте используйте SQLite / PostgreSQL
users_db = {
    # user_id: {"balance": 0.0, "purchases": []}
}

# Каталог товаров
CATALOG = {
    "category_1": {
        "name": "📦 Цифровые товары",
        "items": {
            "item_1": {"name": "Товар #1", "price": 150.0, "desc": "Описание товара 1."},
            "item_2": {"name": "Товар #2", "price": 300.0, "desc": "Описание товара 2."},
        },
    },
    "category_2": {
        "name": "🔑 Подписки",
        "items": {
            "item_3": {"name": "Подписка на 1 мес.", "price": 499.0, "desc": "Доступ на месяц."},
        },
    },
}


# Состояния для пополнения баланса
class TopUpStates(StatesGroup):
    waiting_for_amount = State()


# --- Клавиатуры ---
def main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Каталог товаров", callback_data="catalog")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")],
        ]
    )


def back_to_main_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")]
        ]
    )


# --- Хендлеры ---


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "purchases": []}

    await message.answer(
        "👋 **Добро пожаловать в наш магазин!**\n\n"
        "Используйте меню ниже для навигации:",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 **Главное меню:**", reply_markup=main_menu_kb(), parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = users_db.setdefault(user_id, {"balance": 0.0, "purchases": []})

    text = (
        f"👤 **Ваш профиль:**\n\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"💰 **Баланс:** `{user['balance']} руб.`\n"
        f"🛍 **Куплено товаров:** `{len(user['purchases'])}`"
    )
    await callback.message.edit_text(
        text, reply_markup=back_to_main_kb(), parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "topup")
async def cb_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💳 **Пополнение баланса**\n\n"
        "Введите сумму для пополнения (в рублях):",
        reply_markup=back_to_main_kb(),
        parse_mode="Markdown",
    )
    await state.set_state(TopUpStates.waiting_for_amount)
    await callback.answer()


@router.message(TopUpStates.waiting_for_amount)
async def process_topup_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "⚠️ Пожалуйста, введите корректное число больше 0."
        )
        return

    user_id = message.from_user.id
    
    # Здесь можно сделать запрос к платежному шлюзу, используя ваш API_KEY:
    # Например: response = requests.post(..., headers={"Authorization": f"Bearer {API_KEY}"})
    
    # Для примера сразу зачисляем баланс (в продакшене здесь должна быть генерация ссылки на оплату):
    users_db[user_id]["balance"] += amount
    await state.clear()

    await message.answer(
        f"✅ Баланс успешно пополнен на **{amount} руб.**!\n"
        f"Текущий баланс: **{users_db[user_id]['balance']} руб.**",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    keyboard = []
    for cat_id, cat_data in CATALOG.items():
        keyboard.append(
            [InlineKeyboardButton(text=cat_data["name"], callback_data=f"cat_{cat_id}")]
        )
    keyboard.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")])

    await callback.message.edit_text(
        "🛍 **Выберите категорию товаров:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery):
    cat_id = callback.data.split("_")[1]
    category = CATALOG.get(cat_id)

    keyboard = []
    for item_id, item_data in category["items"].items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{item_data['name']} — {item_data['price']} руб.",
                    callback_data=f"item_{item_id}",
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="catalog")])

    await callback.message.edit_text(
        f"📂 Категория: **{category['name']}**\nВыберите товар:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("item_"))
async def cb_item(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    
    # Ищем товар в каталоге
    selected_item = None
    for cat in CATALOG.values():
        if item_id in cat["items"]:
            selected_item = cat["items"][item_id]
            break

    if not selected_item:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_{item_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="catalog")],
        ]
    )

    await callback.message.edit_text(
        f"📦 **{selected_item['name']}**\n\n"
        f"📝 Описание: {selected_item['desc']}\n"
        f"💵 Стоимость: **{selected_item['price']} руб.**",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = users_db.setdefault(user_id, {"balance": 0.0, "purchases": []})

    # Ищем товар
    selected_item = None
    for cat in CATALOG.values():
        if item_id in cat["items"]:
            selected_item = cat["items"][item_id]
            break

    if user["balance"] < selected_item["price"]:
        await callback.answer(
            "❌ Недостаточно средств на балансе! Пополните счет.", show_alert=True
        )
        return

    # Списываем средства и добавляем покупку
    user["balance"] -= selected_item["price"]
    user["purchases"].append(selected_item["name"])

    await callback.message.edit_text(
        f"✅ **Покупка успешно совершена!**\n\n"
        f"Вы приобрели: {selected_item['name']}\n"
        f"Списано: {selected_item['price']} руб.\n"
        f"Остаток на балансе: {user['balance']} руб.",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())