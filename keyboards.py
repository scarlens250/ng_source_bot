# keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from database import get_config

def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📦 Купить трафик", callback_data="buy_traffic"))
    builder.row(types.InlineKeyboardButton(text="💰 Баланс", callback_data="balance"))
    builder.row(types.InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals"),
                types.InlineKeyboardButton(text="📋 Заказы", callback_data="my_orders"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
                types.InlineKeyboardButton(text="❓ Помощь", callback_data="help"))
    builder.row(types.InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/ng_reklama_support"))
    if get_config('test_mode') == 'True':
        builder.row(types.InlineKeyboardButton(text="🧪 ТЕСТОВЫЙ РЕЖИМ", callback_data="test_mode_info"))
    return builder.as_markup()

def back_kb(callback_data="main_menu"):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data))
    return builder.as_markup()

def deposit_methods_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🪙 TRC-20", callback_data="deposit_trc20"),
        types.InlineKeyboardButton(text="🪙 BEP-20", callback_data="deposit_bep20"),
        types.InlineKeyboardButton(text="🪙 TON", callback_data="deposit_ton")
    )
    builder.row(types.InlineKeyboardButton(text="💳 Банковская карта", callback_data="deposit_card"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def filter_kb(current_geo, current_sex, current_age, current_avatar):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"🌍 ГЕО: {current_geo}", callback_data="filter_geo"))
    builder.row(types.InlineKeyboardButton(text=f"👤 Пол: {current_sex}", callback_data="filter_sex"))
    builder.row(types.InlineKeyboardButton(text=f"🎂 Возраст: {current_age}", callback_data="filter_age"))
    builder.row(types.InlineKeyboardButton(text=f"🖼️ Аватар: {current_avatar}", callback_data="filter_avatar"))
    builder.row(types.InlineKeyboardButton(text="✅ Далее", callback_data="continue_to_price"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"))
    return builder.as_markup()

def topics_kb():
    builder = InlineKeyboardBuilder()
    topics = ["💬 Чат", "📰 Новости", "🎮 Игры", "💰 Крипта", "📚 Образование", "💼 Бизнес", "❤️ Отношения", "🎵 Музыка", "🎬 Юмор", "✏️ Своя"]
    for topic in topics:
        builder.row(types.InlineKeyboardButton(text=topic, callback_data=f"topic_{topic}"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="buy_traffic"))
    return builder.as_markup()

def moderation_kb(order_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"moder_approve_{order_id}"),
        types.InlineKeyboardButton(text="⚠️ Оплата есть, канал не подходит", callback_data=f"moder_reject_channel_{order_id}"),
        types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"moder_reject_{order_id}")
    )
    return builder.as_markup()