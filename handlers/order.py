# handlers/order.py
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_user, get_config
from keyboards import back_kb, filter_kb, topics_kb
from config import MIN_ORDER_COUNT, MAX_ORDER_COUNT, get_bonus_info

class OrderStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_topic = State()
    waiting_for_count = State()
    tuning = State()
    waiting_for_payment = State()

def get_current_price(data):
    filter_price = float(get_config('filter_surcharge') or 0.5)
    base_price = float(get_config('base_price') or 2.0)
    
    surcharge = 0
    if data.get('geo') != "🌍 Любой":
        surcharge += filter_price
    if data.get('sex') != "👥 Любой":
        surcharge += filter_price
    if data.get('age') != "👥 Любой":
        surcharge += filter_price
    if data.get('has_avatar') != "🖼️ Любой":
        surcharge += filter_price
    
    unit_p = base_price + surcharge
    total = unit_p * data.get('count', 0)
    
    return unit_p, total

def register_order_handlers(dp: Dispatcher):
    
    @dp.callback_query(F.data == "buy_traffic")
    async def buy_traffic_handler(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text(
            "<b>📦 Оформление заказа</b>\n\n"
            f"<b>Шаг 1 из 5: Ссылка на канал</b>\n\n"
            "Отправьте ссылку на ваш Telegram канал:\n"
            "<code>t.me/username</code>",
            reply_markup=back_kb(), parse_mode="HTML"
        )
        await state.set_state(OrderStates.waiting_for_link)

    @dp.message(OrderStates.waiting_for_link)
    async def process_order_link(message: types.Message, state: FSMContext):
        link = message.text.strip()
        if "t.me/" not in link:
            await message.answer("❌ Неверная ссылка! Нужно t.me/...")
            return
        
        await state.update_data(link=link)
        await message.answer(
            "<b>Шаг 2 из 5: Тематика канала</b>\n\n"
            "Выберите тематику:",
            reply_markup=topics_kb(), parse_mode="HTML"
        )
        await state.set_state(OrderStates.waiting_for_topic)

    @dp.callback_query(F.data.startswith("topic_"))
    async def process_topic(callback: types.CallbackQuery, state: FSMContext):
        topic = callback.data.replace("topic_", "")
        if topic == "✏️ Своя":
            await callback.message.edit_text(
                "Напишите тематику вашего канала:",
                reply_markup=back_kb("buy_traffic"), parse_mode="HTML"
            )
            await state.set_state(OrderStates.waiting_for_topic)
            return
        
        await state.update_data(topic=topic)
        await callback.message.edit_text(
            f"<b>Шаг 3 из 5: Количество подписчиков</b>\n\n"
            f"Тематика: {topic}\n\n"
            f"Введите количество (от {MIN_ORDER_COUNT} до {MAX_ORDER_COUNT}):",
            reply_markup=back_kb("buy_traffic"), parse_mode="HTML"
        )
        await state.set_state(OrderStates.waiting_for_count)

    @dp.message(OrderStates.waiting_for_topic)
    async def process_custom_topic(message: types.Message, state: FSMContext):
        await state.update_data(topic=message.text.strip())
        await message.answer(
            f"<b>Шаг 3 из 5: Количество подписчиков</b>\n\n"
            f"Введите количество (от {MIN_ORDER_COUNT} до {MAX_ORDER_COUNT}):",
            reply_markup=back_kb("buy_traffic"), parse_mode="HTML"
        )
        await state.set_state(OrderStates.waiting_for_count)

    @dp.message(OrderStates.waiting_for_count)
    async def process_order_count(message: types.Message, state: FSMContext):
        if not message.text.isdigit():
            await message.answer("❌ Введите число!")
            return
        
        count = int(message.text)
        if count < MIN_ORDER_COUNT or count > MAX_ORDER_COUNT:
            await message.answer(f"❌ Количество должно быть от {MIN_ORDER_COUNT} до {MAX_ORDER_COUNT}!")
            return
        
        await state.update_data(count=count)
        await state.update_data(geo="🌍 Любой")
        await state.update_data(sex="👥 Любой")
        await state.update_data(age="👥 Любой")
        await state.update_data(has_avatar="🖼️ Любой")
        
        await show_filters(message, state)

    async def show_filters(message, state: FSMContext):
        data = await state.get_data()
        unit_p, total = get_current_price(data)
        
        builder = filter_kb(
            data.get('geo', '🌍 Любой'), 
            data.get('sex', '👥 Любой'), 
            data.get('age', '👥 Любой'), 
            data.get('has_avatar', '🖼️ Любой')
        )
        
        text = (
            f"<b>⚙️ Шаг 4 из 5: Настройка фильтров</b>\n\n"
            f"📎 <b>Канал:</b> {data.get('link', '—')}\n"
            f"🎯 <b>Тематика:</b> {data.get('topic', '—')}\n"
            f"👥 <b>Количество:</b> {data.get('count', 0)} шт\n\n"
            f"<b>💰 Цена:</b>\n"
            f"  • {unit_p:.2f} грн/подписчик\n"
            f"  • <b>Итого: {total:.2f} грн</b>\n\n"
            f"<b>🔍 Фильтры:</b>\n"
            f"  🌍 ГЕО: {data.get('geo', '🌍 Любой')}\n"
            f"  👤 Пол: {data.get('sex', '👥 Любой')}\n"
            f"  🎂 Возраст: {data.get('age', '👥 Любой')}\n"
            f"  🖼️ Аватар: {data.get('has_avatar', '🖼️ Любой')}\n\n"
            f"<i>Каждый выбранный фильтр добавляет +{get_config('filter_surcharge') or 0.5} грн</i>\n\n"
            f"Нажмите на фильтр чтобы изменить 👇"
        )
        
        if isinstance(message, types.CallbackQuery):
            await message.message.edit_text(text, reply_markup=builder, parse_mode="HTML")
            await message.answer()
        else:
            await message.answer(text, reply_markup=builder, parse_mode="HTML")
        await state.set_state(OrderStates.tuning)

    @dp.callback_query(F.data.startswith("filter_"))
    async def filter_options(callback: types.CallbackQuery):
        filter_type = callback.data.replace("filter_", "")
        
        builder = InlineKeyboardBuilder()
        if filter_type == "geo":
            opts = ["🌍 Любой", "🇺🇦 Украина", "🇷🇺 Россия", "🇧🇾 Беларусь", "🌍 СНГ", "🌍 Европа"]
            key = "set_geo"
        elif filter_type == "sex":
            opts = ["👥 Любой", "👨 Мужской", "👩 Женский"]
            key = "set_sex"
        elif filter_type == "age":
            opts = ["👥 Любой", "📚 12-17", "🎓 18-25", "👔 25+"]
            key = "set_age"
        else:
            opts = ["🖼️ Любой", "✅ Есть аватар", "❌ Нет аватара"]
            key = "set_avatar"
        
        for o in opts:
            builder.row(types.InlineKeyboardButton(text=o, callback_data=f"{key}:{o}"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_filters"))
        
        await callback.message.edit_text(f"🎯 <b>Выберите {filter_type}:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("set_"))
    async def save_filter(callback: types.CallbackQuery, state: FSMContext):
        parts = callback.data.split(":", 1)
        if len(parts) != 2:
            return
        
        field = parts[0].replace("set_", "")
        val = parts[1]
        
        if field == "geo":
            await state.update_data(geo=val)
        elif field == "sex":
            await state.update_data(sex=val)
        elif field == "age":
            await state.update_data(age=val)
        elif field == "avatar":
            await state.update_data(has_avatar=val)
        
        await show_filters(callback, state)

    @dp.callback_query(F.data == "back_to_filters")
    async def back_to_filters(callback: types.CallbackQuery, state: FSMContext):
        await show_filters(callback, state)

    @dp.callback_query(F.data == "continue_to_price")
    async def continue_to_price(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        balance, _, _, _ = get_user(callback.from_user.id)
        unit_p, total = get_current_price(data)
        
        await state.update_data(
            link=data.get('link'),
            topic=data.get('topic'),
            count=data.get('count'),
            geo=data.get('geo', '🌍 Любой'),
            sex=data.get('sex', '👥 Любой'),
            age=data.get('age', '👥 Любой'),
            has_avatar=data.get('has_avatar', '🖼️ Любой'),
            final_amount=total
        )
        
        current_bonus, next_need, next_bonus = get_bonus_info(total)
        
        bonus_text = ""
        if current_bonus > 0:
            bonus_text = f"\n✨ <i>К вашей сумме применён бонус +{current_bonus}%!</i>"
            if next_need > 0 and next_need > 100:
                bonus_text += f"\n💫 <i>До бонуса +{next_bonus}% не хватает {next_need:.0f} грн</i>"
        else:
            if next_need > 0:
                bonus_text = f"\n⭐️ <i>До бонуса +{next_bonus}% не хватает {next_need:.0f} грн</i>"
                bonus_text += f"\n💡 <i>Пополните баланс и получите бонус!</i>"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="💳 С баланса", callback_data="pay_balance"),
            types.InlineKeyboardButton(text="🪙 USDT", callback_data="pay_crypto"),
            types.InlineKeyboardButton(text="💳 Картой", callback_data="pay_card")
        )
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_filters"))
        
        await callback.message.edit_text(
            f"<b>💰 Шаг 5 из 5: Оплата</b>\n\n"
            f"📎 {data.get('link', '—')}\n"
            f"🎯 {data.get('topic', '—')}\n"
            f"👥 {data.get('count', 0)} шт\n\n"
            f"💵 <b>Сумма: {total:.2f} грн</b>\n"
            f"{bonus_text}\n\n"
            f"💰 <b>Баланс: {balance:.2f} грн</b>\n\n"
            f"Выберите способ оплаты:",
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )
        await state.set_state(OrderStates.waiting_for_payment)