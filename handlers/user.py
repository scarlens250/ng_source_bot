# handlers/user.py
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from datetime import datetime
import sqlite3

from config import MIN_ORDER_COUNT, MAX_ORDER_COUNT, MIN_DEPOSIT_UAH, MIN_DEPOSIT_USDT
from database import (
    get_user, update_balance, update_user_stats, is_blocked,
    get_user_orders, get_order_stats, get_config
)
from keyboards import main_menu_kb, back_kb, deposit_methods_kb

def register_user_handlers(dp: Dispatcher, bot: Bot):
    
    @dp.message(CommandStart())
    async def start_handler(message: types.Message):
        if await is_blocked(message.from_user.id):
            await message.answer("🚫 <b>Ваш аккаунт заблокирован!</b>", parse_mode="HTML")
            return
        
        args = message.text.split()
        ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (message.from_user.id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('INSERT INTO users (user_id, username, referrer_id, registration_date, balance, last_activity) VALUES (?, ?, ?, ?, ?, ?)',
                           (message.from_user.id, message.from_user.username, ref_id, datetime.now().isoformat(), 0, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        balance, _, total_spent, total_orders = await get_user(message.from_user.id)
        
        await message.answer(
            f"<b>🚀 Добро пожаловать в N-G SOURCE!</b>\n\n"
            f"💰 <b>Баланс:</b> {balance:.2f} грн\n"
            f"📊 <b>Заказов:</b> {total_orders}\n\n"
            f"<i>Выберите действие в меню 👇</i>",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "help")
    async def help_handler(callback: types.CallbackQuery):
        await callback.message.edit_text(
            f"<b>❓ Помощь и инструкция</b>\n\n"
            f"<b>📦 Как купить трафик:</b>\n"
            f"1️⃣ Нажмите «Купить трафик»\n"
            f"2️⃣ Укажите ссылку на канал\n"
            f"3️⃣ Тематику канала\n"
            f"4️⃣ Количество подписчиков (от {MIN_ORDER_COUNT} до {MAX_ORDER_COUNT})\n"
            f"5️⃣ Настройте фильтры\n"
            f"6️⃣ Оплатите заказ\n\n"
            f"<b>💰 Пополнение баланса:</b>\n"
            f"• Минимальная сумма: {MIN_DEPOSIT_UAH} грн / {MIN_DEPOSIT_USDT} USDT\n\n"
            f"<b>🎁 Бонусы при пополнении:</b>\n"
            f"  • от 500 грн (≈12.5 USDT) → +3%\n"
            f"  • от 1000 грн (≈25 USDT) → +5%\n"
            f"  • от 2000 грн (≈50 USDT) → +7%\n"
            f"  • от 3500 грн (≈87.5 USDT) → +8%\n"
            f"  • от 5000 грн (≈125 USDT) → +10%\n\n"
            f"<b>👥 Рефералы:</b> 15% от заказов друзей\n\n"
            f"<b>📞 Поддержка:</b> @flsdlfdsllfbot",
            reply_markup=back_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "balance")
    async def balance_handler(callback: types.CallbackQuery):
        balance, _, _, _ = await get_user(callback.from_user.id)
        
        await callback.message.edit_text(
            f"<b>💰 Мой баланс</b>\n\n"
            f"Доступно: {balance:.2f} грн\n\n"
            f"<b>🎁 Бонусы при пополнении:</b>\n"
            f"  • от 500 грн (≈12.5 USDT) → +3%\n"
            f"  • от 1000 грн (≈25 USDT) → +5%\n"
            f"  • от 2000 грн (≈50 USDT) → +7%\n"
            f"  • от 3500 грн (≈87.5 USDT) → +8%\n"
            f"  • от 5000 грн (≈125 USDT) → +10%\n\n"
            f"<i>Чем больше сумма, тем выше бонус!</i>\n\n"
            f"📌 <b>Минимальное пополнение:</b> {MIN_DEPOSIT_UAH} грн / {MIN_DEPOSIT_USDT} USDT\n\n"
            f"<b>💳 Выберите способ пополнения:</b>",
            reply_markup=deposit_methods_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "stats")
    async def stats_handler(callback: types.CallbackQuery):
        orders = await get_user_orders(callback.from_user.id)
        orders_count, total_amount = await get_order_stats(callback.from_user.id)
        balance, _, total_spent, _ = await get_user(callback.from_user.id)
        
        status_counts = {'pending': 0, 'approved': 0, 'rejected': 0, 'completed': 0}
        for order in orders:
            status_counts[order[5]] = status_counts.get(order[5], 0) + 1
        
        text = f"<b>📊 Моя статистика</b>\n\n"
        text += f"<b>💰 Финансы:</b>\n"
        text += f"  • Баланс: {balance:.2f} грн\n"
        text += f"  • Потрачено: {total_spent:.2f} грн\n"
        text += f"  • Средний чек: {total_amount/orders_count if orders_count > 0 else 0:.2f} грн\n\n"
        text += f"<b>📦 Заказы:</b>\n"
        text += f"  • ⏳ На модерации: {status_counts['pending']}\n"
        text += f"  • ✅ В работе: {status_counts['approved']}\n"
        text += f"  • 🎉 Выполнено: {status_counts['completed']}\n"
        text += f"  • ❌ Отклонено: {status_counts['rejected']}"
        
        await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "my_orders")
    async def my_orders_handler(callback: types.CallbackQuery):
        orders = await get_user_orders(callback.from_user.id)
        
        if not orders:
            await callback.message.edit_text(
                "📋 <b>У вас пока нет заказов</b>\n\nСделайте первый заказ!",
                reply_markup=back_kb(), parse_mode="HTML"
            )
            return
        
        status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌', 'completed': '🎉'}
        status_text = {'pending': 'На модерации', 'approved': 'В работе', 'rejected': 'Отклонён', 'completed': 'Завершён'}
        
        text = "<b>📋 Мои заказы</b>\n\n"
        for order in orders[:5]:
            emoji = status_emoji.get(order[5], '❓')
            status_txt = status_text.get(order[5], order[5])
            text += f"{emoji} <b>#{order[0]}</b>\n   👥 {order[3]} шт | {order[4]:.0f} грн\n   📌 {status_txt}\n\n"
        
        await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "referrals")
    async def referrals_handler(callback: types.CallbackQuery):
        me = await bot.get_me()
        link = f"https://t.me/{me.username}?start={callback.from_user.id}"
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (callback.from_user.id,))
        ref_count = cursor.fetchone()[0]
        conn.close()
        
        await callback.message.edit_text(
            f"<b>👥 Реферальная программа</b>\n\n"
            f"<b>Ваша ссылка:</b>\n<code>{link}</code>\n\n"
            f"<b>📊 Статистика:</b>\n"
            f"  • Приглашено: {ref_count}\n"
            f"  • Бонус: 15% от заказов рефералов",
            reply_markup=back_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "test_mode_info")
    async def test_mode_info(callback: types.CallbackQuery):
        test_mode = await get_config('test_mode') == 'True'
        await callback.message.edit_text(
            f"<b>🧪 Тестовый режим: {'ВКЛЮЧЁН' if test_mode else 'ВЫКЛЮЧЕН'}</b>\n\n"
            f"• Деньги {'НЕ' if test_mode else ''} списываются с баланса\n"
            f"• Заказы идут на модерацию\n\n"
            f"⚠️ <b>В админ-панели можно переключить режим</b>",
            reply_markup=back_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "main_menu")
    async def to_main_menu(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        balance, _, total_spent, total_orders = await get_user(callback.from_user.id)
        
        await callback.message.edit_text(
            f"<b>🚀 N-G SOURCE</b>\n\n"
            f"💰 <b>Баланс:</b> {balance:.2f} грн\n"
            f"📊 <b>Заказов:</b> {total_orders}\n\n"
            f"<i>Выберите действие в меню 👇</i>",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )