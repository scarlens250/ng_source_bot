# admin.py - Админ-панель для бота
from aiogram import types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import asyncio
from datetime import datetime
import shutil

# Состояния для админки
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_user_search = State()
    waiting_balance_change = State()
    waiting_price_change = State()
    waiting_usdt_rate = State()
    waiting_ref_percent = State()
    waiting_filter_price = State()
    waiting_test_balance = State()

# Вспомогательные функции для админки
def get_config(key):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def set_config(key, value):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE config SET value = ?, updated_at = ? WHERE key = ?',
                   (str(value), datetime.now().isoformat(), key))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, balance, total_spent, total_orders, registration_date FROM users ORDER BY total_spent DESC')
    res = cursor.fetchall()
    conn.close()
    return res

def update_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def set_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()[0]
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status IN ("approved", "completed")')
    total_volume = cursor.fetchone()[0]
    cursor.execute('SELECT COALESCE(AVG(amount), 0) FROM orders WHERE status IN ("approved", "completed")')
    avg_order = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
    pending_orders = cursor.fetchone()[0]
    conn.close()
    return total_users, total_orders, total_volume, avg_order, pending_orders

def get_all_orders(limit=50, status=None):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    if status:
        cursor.execute('''SELECT order_id, user_id, link, channel_name, count, amount, status, date 
                          FROM orders WHERE status = ? ORDER BY date DESC LIMIT ?''', (status, limit))
    else:
        cursor.execute('''SELECT order_id, user_id, link, channel_name, count, amount, status, date 
                          FROM orders ORDER BY date DESC LIMIT ?''', (limit,))
    res = cursor.fetchall()
    conn.close()
    return res

def update_order_status(order_id, status, admin_id=None):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE orders SET status = ?, moderated_at = ?, moderated_by = ? WHERE order_id = ?''',
                   (status, datetime.now().isoformat(), admin_id, order_id))
    conn.commit()
    conn.close()

def get_user_info(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, balance, total_spent, total_orders, referrer_id, registration_date, last_activity FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def block_user(user_id, blocked=True):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS blocked_users (user_id INTEGER PRIMARY KEY)''')
    if blocked:
        cursor.execute('INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)', (user_id,))
    else:
        cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def is_blocked(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM blocked_users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# Клавиатуры админки
def admin_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders"),
                types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"))
    builder.row(types.InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                types.InlineKeyboardButton(text="💬 Рассылка", callback_data="admin_broadcast"))
    builder.row(types.InlineKeyboardButton(text="💾 Бэкап БД", callback_data="admin_backup"),
                types.InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"))
    return builder.as_markup()

def admin_users_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user"))
    builder.row(types.InlineKeyboardButton(text="📋 Топ по тратам", callback_data="admin_top_users"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()

def admin_orders_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⏳ На модерации", callback_data="admin_orders_pending"))
    builder.row(types.InlineKeyboardButton(text="✅ Выполненные", callback_data="admin_orders_completed"))
    builder.row(types.InlineKeyboardButton(text="❌ Отклонённые", callback_data="admin_orders_rejected"))
    builder.row(types.InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_orders_all"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()

def admin_settings_kb():
    test_mode = get_config('test_mode') == 'True'
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text=f"🧪 Тестовый режим: {'ВКЛ' if test_mode else 'ВЫКЛ'}",
        callback_data="admin_toggle_test"
    ))
    builder.row(types.InlineKeyboardButton(text="💰 Курс USDT", callback_data="admin_set_usdt"))
    builder.row(types.InlineKeyboardButton(text="💵 Базовая цена", callback_data="admin_set_base_price"))
    builder.row(types.InlineKeyboardButton(text="➕ Доплата за фильтр", callback_data="admin_set_filter_price"))
    builder.row(types.InlineKeyboardButton(text="👥 Реферальный %", callback_data="admin_set_ref_percent"))
    builder.row(types.InlineKeyboardButton(text="🎁 Тест. баланс", callback_data="admin_set_test_balance"))
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"))
    return builder.as_markup()

def back_kb(callback_data="admin_panel"):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data))
    return builder.as_markup()

# Регистрация всех админ-обработчиков
def register_admin_handlers(dp, ADMIN_ID):
    
    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            await message.answer("⛔ Доступ запрещён!")
            return
        
        total_users, total_orders, total_volume, avg_order, pending_orders = get_stats()
        test_mode = get_config('test_mode') == 'True'
        
        text = (
            f"<b>🎛️ Админ-панель</b>\n\n"
            f"<b>📊 Статистика:</b>\n"
            f"  • 👥 Пользователей: {total_users}\n"
            f"  • 📦 Заказов: {total_orders}\n"
            f"  • ⏳ На модерации: {pending_orders}\n"
            f"  • 💰 Оборот: {total_volume:.0f} грн\n"
            f"  • 💵 Средний чек: {avg_order:.0f} грн\n\n"
            f"<b>⚙️ Настройки:</b>\n"
            f"  • 🧪 Тест. режим: {'ВКЛ' if test_mode else 'ВЫКЛ'}\n"
            f"  • 💵 Курс USDT: {get_config('usd_to_uah')} грн\n"
            f"  • 💎 Базовая цена: {get_config('base_price')} грн\n"
            f"  • 🎯 Доплата за фильтр: {get_config('filter_surcharge')} грн\n"
            f"  • 👥 Реф. %: {float(get_config('ref_percent')) * 100}%\n\n"
            f"<i>Выберите действие:</i>"
        )
        await message.answer(text, reply_markup=admin_kb(), parse_mode="HTML")

    # ========== КОМАНДА /pay ==========
    @dp.message(Command("pay"))
    async def admin_pay(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ Использование: /pay ID СУММА\nПример: /pay 123456789 100")
            return
        
        try:
            user_id = int(args[1])
            amount = float(args[2])
            update_balance(user_id, amount)
            await message.answer(f"✅ Начислено {amount:.2f} грн пользователю {user_id}")
            try:
                await bot.send_message(user_id, f"💰 Ваш баланс пополнен на {amount:.2f} грн!")
            except:
                pass
        except ValueError:
            await message.answer("❌ Ошибка! ID и сумма должны быть числами")

    # ========== КОМАНДА /setbal ==========
    @dp.message(Command("setbal"))
    async def admin_setbal(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ Использование: /setbal ID СУММА\nПример: /setbal 123456789 500")
            return
        
        try:
            user_id = int(args[1])
            amount = float(args[2])
            set_balance(user_id, amount)
            await message.answer(f"✅ Установлен баланс {amount:.2f} грн пользователю {user_id}")
            try:
                await bot.send_message(user_id, f"💰 Ваш баланс установлен на {amount:.2f} грн администратором!")
            except:
                pass
        except ValueError:
            await message.answer("❌ Ошибка! ID и сумма должны быть числами")

    # ========== КОМАНДА /users ==========
    @dp.message(Command("users"))
    async def admin_users_list(message: types.Message):
        if message.from_user.id != ADMIN_ID:
            return
        
        users = get_all_users()
        if not users:
            await message.answer("❌ Пользователей пока нет")
            return
        
        text = "<b>👥 Список пользователей</b>\n\n"
        for user in users[:20]:
            text += f"🆔 {user[0]} | @{user[1] or '—'} | 💰 {user[2]:.0f} грн | 💸 {user[3]:.0f} грн\n"
        
        if len(users) > 20:
            text += f"\n<i>... и ещё {len(users) - 20} пользователей</i>"
        
        await message.answer(text, parse_mode="HTML")

    @dp.callback_query(F.data == "admin_panel")
    async def admin_panel_callback(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        total_users, total_orders, total_volume, avg_order, pending_orders = get_stats()
        test_mode = get_config('test_mode') == 'True'
        text = (
            f"<b>🎛️ Админ-панель</b>\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"📦 Заказов: {total_orders} | ⏳ В работе: {pending_orders}\n"
            f"💰 Оборот: {total_volume:.0f} грн\n\n"
            f"🧪 Тест. режим: {'ВКЛ' if test_mode else 'ВЫКЛ'}"
        )
        await callback.message.edit_text(text, reply_markup=admin_kb(), parse_mode="HTML")

    # Пользователи
    @dp.callback_query(F.data == "admin_users")
    async def admin_users(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        users = get_all_users()
        text = f"<b>👥 Пользователи ({len(users)})</b>\n\n"
        for user in users[:10]:
            text += f"🆔 {user[0]} | @{user[1] or '—'} | 💰 {user[2]:.0f} грн\n"
        if len(users) > 10:
            text += f"\n<i>... и ещё {len(users) - 10}</i>"
        await callback.message.edit_text(text, reply_markup=admin_users_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "admin_find_user")
    async def admin_find_user(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        await callback.message.edit_text(
            "<b>🔍 Поиск пользователя</b>\n\nВведите ID или @username:",
            reply_markup=back_kb("admin_users"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_user_search)

    @dp.message(AdminStates.waiting_user_search)
    async def admin_user_search_result(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        search = message.text.strip()
        if search.startswith('@'):
            search = search[1:]
        
        if search.isdigit():
            user = get_user_info(int(search))
        else:
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, balance, total_spent, total_orders, referrer_id, registration_date, last_activity FROM users WHERE username = ?', (search,))
            user = cursor.fetchone()
            conn.close()
        
        if not user:
            await message.answer("❌ Пользователь не найден!", reply_markup=admin_users_kb())
            await state.clear()
            return
        
        blocked = "🚫 Заблокирован" if is_blocked(user[0]) else "✅ Активен"
        text = (
            f"<b>👤 Пользователь</b>\n\n"
            f"🆔 ID: <code>{user[0]}</code>\n"
            f"👤 Username: @{user[1] or '—'}\n"
            f"📊 Статус: {blocked}\n"
            f"💰 Баланс: {user[2]:.2f} грн\n"
            f"💸 Потрачено: {user[3]:.2f} грн\n"
            f"📦 Заказов: {user[4]}\n"
            f"📅 Регистрация: {user[6][:10] if user[6] else '—'}"
        )
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="💰 +100", callback_data=f"admin_add_100_{user[0]}"),
                    types.InlineKeyboardButton(text="💰 -100", callback_data=f"admin_sub_100_{user[0]}"))
        builder.row(types.InlineKeyboardButton(text="💎 Установить баланс", callback_data=f"admin_set_balance_{user[0]}"))
        builder.row(types.InlineKeyboardButton(text="🚫 Блок" if not is_blocked(user[0]) else "✅ Разблок", 
                                               callback_data=f"admin_toggle_block_{user[0]}"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_users"))
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()

    @dp.callback_query(F.data.startswith("admin_add_100_"))
    async def admin_add_100(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        user_id = int(callback.data.split("_")[3])
        update_balance(user_id, 100)
        await callback.answer("✅ +100 грн!", show_alert=True)
        await admin_find_user(callback, AdminStates.waiting_user_search)

    @dp.callback_query(F.data.startswith("admin_sub_100_"))
    async def admin_sub_100(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        user_id = int(callback.data.split("_")[3])
        update_balance(user_id, -100)
        await callback.answer("✅ -100 грн!", show_alert=True)
        await admin_find_user(callback, AdminStates.waiting_user_search)

    @dp.callback_query(F.data.startswith("admin_set_balance_"))
    async def admin_set_balance_prompt(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        user_id = int(callback.data.split("_")[3])
        await state.update_data(target_user_id=user_id)
        await callback.message.edit_text(
            f"💎 <b>Установка баланса для пользователя ID: {user_id}</b>\n\n"
            f"Введите новую сумму баланса:",
            reply_markup=back_kb("admin_users"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_balance_change)

    @dp.message(AdminStates.waiting_balance_change)
    async def admin_set_balance_execute(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            amount = float(message.text.strip().replace(',', '.'))
            data = await state.get_data()
            user_id = data.get('target_user_id')
            if user_id:
                set_balance(user_id, amount)
                try:
                    await bot.send_message(user_id, f"💰 Администратор установил ваш баланс: {amount:.2f} грн")
                except:
                    pass
                await message.answer(f"✅ Баланс пользователя {user_id} установлен: {amount:.2f} грн", reply_markup=admin_users_kb())
        except ValueError:
            await message.answer("❌ Ошибка! Введите число (например: 1000 или 500.50)", reply_markup=admin_users_kb())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=admin_users_kb())
        await state.clear()

    @dp.callback_query(F.data.startswith("admin_toggle_block_"))
    async def admin_toggle_block(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        user_id = int(callback.data.split("_")[3])
        blocked = not is_blocked(user_id)
        block_user(user_id, blocked)
        await callback.answer(f"✅ {'Заблокирован' if blocked else 'Разблокирован'}!", show_alert=True)
        await admin_find_user(callback, AdminStates.waiting_user_search)

    # Настройки
    @dp.callback_query(F.data == "admin_settings")
    async def admin_settings(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            "<b>⚙️ Настройки</b>\n\nВыберите параметр:",
            reply_markup=admin_settings_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "admin_toggle_test")
    async def admin_toggle_test(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        current = get_config('test_mode') == 'True'
        set_config('test_mode', str(not current))
        await callback.answer(f"✅ Тест. режим {'ВКЛ' if not current else 'ВЫКЛ'}!", show_alert=True)
        await admin_settings(callback)

    @dp.callback_query(F.data == "admin_set_usdt")
    async def admin_set_usdt(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            f"💰 Текущий курс: {get_config('usd_to_uah')} грн\n\nВведите новый курс:",
            reply_markup=back_kb("admin_settings"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_usdt_rate)

    @dp.callback_query(F.data == "admin_set_base_price")
    async def admin_set_base_price(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            f"💵 Текущая цена: {get_config('base_price')} грн\n\nВведите новую цену:",
            reply_markup=back_kb("admin_settings"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_price_change)

    @dp.callback_query(F.data == "admin_set_filter_price")
    async def admin_set_filter_price(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            f"➕ Текущая доплата: {get_config('filter_surcharge')} грн\n\nВведите новую сумму:",
            reply_markup=back_kb("admin_settings"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_filter_price)

    @dp.callback_query(F.data == "admin_set_ref_percent")
    async def admin_set_ref_percent(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        current = float(get_config('ref_percent')) * 100
        await callback.message.edit_text(
            f"👥 Текущий процент: {current:.0f}%\n\nВведите новый (1-50):",
            reply_markup=back_kb("admin_settings"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_ref_percent)

    @dp.callback_query(F.data == "admin_set_test_balance")
    async def admin_set_test_balance(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            "🎁 <b>Тестовый баланс для новых пользователей</b>\n\n"
            f"Текущий: {get_config('test_balance') if get_config('test_balance') else '10000'} грн\n\n"
            "Введите новую сумму (0-100000):",
            reply_markup=back_kb("admin_settings"), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_test_balance)

    @dp.message(AdminStates.waiting_usdt_rate)
    async def set_usdt_rate(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                raise ValueError
            set_config('usd_to_uah', str(value))
            await message.answer(f"✅ Курс USDT: {value} грн", reply_markup=admin_settings_kb())
        except:
            await message.answer("❌ Ошибка! Введите число >0", reply_markup=admin_settings_kb())
        await state.clear()

    @dp.message(AdminStates.waiting_price_change)
    async def set_base_price(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                raise ValueError
            set_config('base_price', str(value))
            await message.answer(f"✅ Базовая цена: {value} грн", reply_markup=admin_settings_kb())
        except:
            await message.answer("❌ Ошибка! Введите число", reply_markup=admin_settings_kb())
        await state.clear()

    @dp.message(AdminStates.waiting_filter_price)
    async def set_filter_price(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value < 0:
                raise ValueError
            set_config('filter_surcharge', str(value))
            await message.answer(f"✅ Доплата за фильтр: {value} грн", reply_markup=admin_settings_kb())
        except:
            await message.answer("❌ Ошибка! Введите число", reply_markup=admin_settings_kb())
        await state.clear()

    @dp.message(AdminStates.waiting_ref_percent)
    async def set_ref_percent(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value < 1 or value > 50:
                raise ValueError
            set_config('ref_percent', str(value / 100))
            await message.answer(f"✅ Реф. процент: {value}%", reply_markup=admin_settings_kb())
        except:
            await message.answer("❌ Ошибка! От 1 до 50", reply_markup=admin_settings_kb())
        await state.clear()

    @dp.message(AdminStates.waiting_test_balance)
    async def set_test_balance(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            value = float(message.text.replace(',', '.'))
            if value < 0 or value > 100000:
                raise ValueError
            set_config('test_balance', str(value))
            await message.answer(f"✅ Тест. баланс: {value} грн", reply_markup=admin_settings_kb())
        except:
            await message.answer("❌ Ошибка! От 0 до 100000", reply_markup=admin_settings_kb())
        await state.clear()

    # Статистика
    @dp.callback_query(F.data == "admin_stats")
    async def admin_stats(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        total_users, total_orders, total_volume, avg_order, pending_orders = get_stats()
        top_users = get_all_users()[:5]
        top_text = ""
        for i, user in enumerate(top_users, 1):
            top_text += f"{i}. @{user[1] or user[0]} — {user[3]:.0f} грн\n"
        text = (
            f"<b>📊 Статистика</b>\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"📦 Заказов: {total_orders} | ⏳ В работе: {pending_orders}\n"
            f"💰 Оборот: {total_volume:.0f} грн\n"
            f"💵 Средний чек: {avg_order:.0f} грн\n\n"
            f"<b>🏆 Топ по тратам:</b>\n{top_text}"
        )
        await callback.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")

    # Заказы
    @dp.callback_query(F.data == "admin_orders")
    async def admin_orders_menu(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            "<b>📦 Заказы</b>\n\nВыберите статус:",
            reply_markup=admin_orders_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data.startswith("admin_orders_"))
    async def admin_orders_list(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        status_map = {
            "pending": "⏳ На модерации",
            "completed": "✅ Выполненные",
            "rejected": "❌ Отклонённые",
            "all": "Все заказы"
        }
        status_key = callback.data.replace("admin_orders_", "")
        status_filter = None if status_key == "all" else status_key
        orders = get_all_orders(20, status_filter)
        if not orders:
            await callback.message.edit_text(
                f"<b>{status_map.get(status_key, 'Заказы')}</b>\n\nНет заказов",
                reply_markup=back_kb("admin_orders"), parse_mode="HTML"
            )
            return
        text = f"<b>{status_map.get(status_key, 'Заказы')} ({len(orders)})</b>\n\n"
        for order in orders:
            emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌', 'completed': '🎉'}.get(order[6], '❓')
            text += f"{emoji} #{order[0]} | {order[4]} шт | {order[5]:.0f} грн\n   👤 {order[1]}\n\n"
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="admin_orders"))
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

    # Рассылка
    @dp.callback_query(F.data == "admin_broadcast")
    async def admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
        if callback.from_user.id != ADMIN_ID:
            return
        await callback.message.edit_text(
            "<b>💬 Рассылка</b>\n\nВведите текст сообщения:\n/отмена - отмена",
            reply_markup=back_kb(), parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_broadcast)

    @dp.message(AdminStates.waiting_broadcast)
    async def send_broadcast(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            return
        if message.text == "/отмена":
            await message.answer("❌ Отменено", reply_markup=admin_kb())
            await state.clear()
            return
        users = get_all_users()
        success = 0
        status_msg = await message.answer(f"⏳ Рассылка {len(users)} пользователям...")
        for user in users:
            try:
                await bot.send_message(user[0], message.text, parse_mode="HTML")
                success += 1
            except:
                pass
            await asyncio.sleep(0.05)
        await status_msg.edit_text(f"✅ Рассылка: {success}/{len(users)}", reply_markup=admin_kb())
        await state.clear()

    # Бэкап
    @dp.callback_query(F.data == "admin_backup")
    async def admin_backup(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            return
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy('bot_database.db', backup_name)
        await callback.message.edit_text(
            f"✅ Бэкап: {backup_name}",
            reply_markup=back_kb(), parse_mode="HTML"
        )