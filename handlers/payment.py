# handlers/payment.py
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import re

from config import (
    ADMIN_ID, USD_TO_UAH, USDT_TRC20, USDT_BEP20, USDT_TON, CARD_NUMBER,
    MIN_DEPOSIT_UAH, MIN_DEPOSIT_USDT, get_deposit_bonus
)
from database import (
    get_user, update_balance, update_user_stats, add_order, get_config,
    update_order_proof, update_order_admin_msg, get_order
)
from keyboards import main_menu_kb, back_kb, moderation_kb

class PaymentStates(StatesGroup):
    waiting_crypto_proof = State()
    waiting_card_proof = State()
    waiting_deposit_crypto_proof = State()
    waiting_deposit_card_proof = State()

def register_payment_handlers(dp: Dispatcher, bot: Bot):
    
    # ========== ПОПОЛНЕНИЕ БАЛАНСА USDT ==========
    
    @dp.callback_query(F.data == "deposit_trc20")
    async def deposit_trc20(callback: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data="deposit_confirmed"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="balance"))
        
        await callback.message.edit_text(
            f"🪙 <b>Пополнение USDT (TRC-20)</b>\n\n"
            f"📤 <b>Наш кошелек:</b>\n"
            f"<code>{USDT_TRC20}</code>\n\n"
            f"📌 <b>Инструкция:</b>\n"
            f"• Отправьте от <b>{MIN_DEPOSIT_USDT} USDT</b> на указанный кошелек\n"
            f"• Это ваш персональный адрес для пополнения\n\n"
            f"⏱ <b>Обычное зачисление:</b> от 1 до 30 минут\n\n"
            f"<b>🎁 Бонусная система (в USDT):</b>\n"
            f"  • от 12.5 USDT → +3%\n"
            f"  • от 25 USDT → +5%\n"
            f"  • от 50 USDT → +7%\n"
            f"  • от 87.5 USDT → +8%\n"
            f"  • от 125 USDT → +10%\n\n"
            f"💎 <b>Чем больше сумма, тем выше бонус!</b>\n\n"
            f"✅ После отправки нажмите «Я оплатил» и пришлите чек",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "deposit_bep20")
    async def deposit_bep20(callback: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data="deposit_confirmed"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="balance"))
        
        await callback.message.edit_text(
            f"🪙 <b>Пополнение USDT (BEP-20)</b>\n\n"
            f"📤 <b>Наш кошелек:</b>\n"
            f"<code>{USDT_BEP20}</code>\n\n"
            f"📌 <b>Инструкция:</b>\n"
            f"• Отправьте от <b>{MIN_DEPOSIT_USDT} USDT</b> на указанный кошелек\n"
            f"• Это ваш персональный адрес для пополнения\n\n"
            f"⏱ <b>Обычное зачисление:</b> от 1 до 30 минут\n\n"
            f"<b>🎁 Бонусная система (в USDT):</b>\n"
            f"  • от 12.5 USDT → +3%\n"
            f"  • от 25 USDT → +5%\n"
            f"  • от 50 USDT → +7%\n"
            f"  • от 87.5 USDT → +8%\n"
            f"  • от 125 USDT → +10%\n\n"
            f"💎 <b>Чем больше сумма, тем выше бонус!</b>\n\n"
            f"✅ После отправки нажмите «Я оплатил» и пришлите чек",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "deposit_ton")
    async def deposit_ton(callback: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data="deposit_confirmed"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="balance"))
        
        await callback.message.edit_text(
            f"🪙 <b>Пополнение USDT (TON)</b>\n\n"
            f"📤 <b>Наш кошелек:</b>\n"
            f"<code>{USDT_TON}</code>\n\n"
            f"📌 <b>Инструкция:</b>\n"
            f"• Отправьте от <b>{MIN_DEPOSIT_USDT} USDT</b> на указанный кошелек\n"
            f"• Это ваш персональный адрес для пополнения\n\n"
            f"⏱ <b>Обычное зачисление:</b> от 1 до 30 минут\n\n"
            f"<b>🎁 Бонусная система (в USDT):</b>\n"
            f"  • от 12.5 USDT → +3%\n"
            f"  • от 25 USDT → +5%\n"
            f"  • от 50 USDT → +7%\n"
            f"  • от 87.5 USDT → +8%\n"
            f"  • от 125 USDT → +10%\n\n"
            f"💎 <b>Чем больше сумма, тем выше бонус!</b>\n\n"
            f"✅ После отправки нажмите «Я оплатил» и пришлите чек",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "deposit_card")
    async def deposit_card(callback: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data="deposit_confirmed_card"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="balance"))
        
        await callback.message.edit_text(
            f"💳 <b>Пополнение картой</b>\n\n"
            f"💳 <b>Номер карты:</b>\n"
            f"<code>{CARD_NUMBER}</code>\n\n"
            f"📌 <b>Инструкция:</b>\n"
            f"• Отправьте от <b>{MIN_DEPOSIT_UAH} грн</b> на указанную карту\n"
            f"• После перевода нажмите «Я оплатил»\n\n"
            f"⏱ <b>Обычное зачисление:</b> от 1 до 30 минут\n\n"
            f"<b>🎁 Бонусная система:</b>\n"
            f"  • от 500 грн → +3%\n"
            f"  • от 1000 грн → +5%\n"
            f"  • от 2000 грн → +7%\n"
            f"  • от 3500 грн → +8%\n"
            f"  • от 5000 грн → +10%\n\n"
            f"✅ После оплаты нажмите «Я оплатил» и пришлите чек",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "deposit_confirmed")
    async def deposit_confirmed(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "📸 <b>Отправьте чек перевода</b>\n\n"
            "В подписи укажите сумму в USDT\n"
            "<i>Пример: 50 USDT TRC-20</i>",
            reply_markup=back_kb("balance"), parse_mode="HTML"
        )
        await state.set_state(PaymentStates.waiting_deposit_crypto_proof)

    @dp.message(PaymentStates.waiting_deposit_crypto_proof, F.photo)
    async def process_deposit_crypto_proof(message: types.Message, state: FSMContext):
        amount_usdt = None
        if message.caption:
            numbers = re.findall(r'[\d\.]+', message.caption)
            for num in numbers:
                try:
                    val = float(num)
                    if MIN_DEPOSIT_USDT <= val <= 10000:
                        amount_usdt = val
                        break
                except:
                    pass
        
        usd_rate = float(await get_config('usd_to_uah') or USD_TO_UAH)
        amount_uah = amount_usdt * usd_rate if amount_usdt else 0
        
        bonus = get_deposit_bonus(amount_uah=amount_uah)
        bonus_amount = amount_uah * bonus / 100
        total = amount_uah + bonus_amount
        
        caption = (
            f"🪙 <b>ПОПОЛНЕНИЕ USDT</b>\n\n"
            f"👤 @{message.from_user.username}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"💰 Сумма: {amount_usdt if amount_usdt else '?'} USDT\n"
            f"💵 По курсу: {amount_uah:.0f} грн\n"
            f"🎁 Бонус {bonus}%: +{bonus_amount:.0f} грн\n"
            f"💎 Итого: <b>{total:.0f} грн</b>\n\n"
            f"📌 Команда для зачисления:\n"
            f"<code>/pay {message.from_user.id} {total:.0f}</code>"
        )
        
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Чек отправлен!</b>\n\n"
            f"💰 Сумма к зачислению: {total:.0f} грн\n\n"
            f"⏱ Ожидайте зачисления средств",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        await state.clear()

    @dp.message(PaymentStates.waiting_deposit_crypto_proof)
    async def invalid_deposit_crypto_proof(message: types.Message):
        await message.answer(
            "❌ <b>Отправьте скриншот!</b>\n\n"
            "Фото + сумма в подписи\n"
            "<i>Пример: 50 USDT TRC-20</i>",
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "deposit_confirmed_card")
    async def deposit_confirmed_card(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "📸 <b>Отправьте чек перевода</b>\n\n"
            "В подписи укажите сумму в грн\n"
            "<i>Пример: 500 грн</i>",
            reply_markup=back_kb("balance"), parse_mode="HTML"
        )
        await state.set_state(PaymentStates.waiting_deposit_card_proof)

    @dp.message(PaymentStates.waiting_deposit_card_proof, F.photo)
    async def process_deposit_card_proof(message: types.Message, state: FSMContext):
        amount_uah = None
        if message.caption:
            numbers = re.findall(r'[\d\.]+', message.caption)
            for num in numbers:
                try:
                    val = float(num)
                    if MIN_DEPOSIT_UAH <= val <= 50000:
                        amount_uah = val
                        break
                except:
                    pass
        
        if not amount_uah:
            await message.answer("❌ Укажите сумму в подписи!\nПример: 500 грн")
            return
        
        bonus = get_deposit_bonus(amount_uah=amount_uah)
        bonus_amount = amount_uah * bonus / 100
        total = amount_uah + bonus_amount
        
        caption = (
            f"💳 <b>ПОПОЛНЕНИЕ КАРТОЙ</b>\n\n"
            f"👤 @{message.from_user.username}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"💰 Сумма: {amount_uah:.0f} грн\n"
            f"🎁 Бонус {bonus}%: +{bonus_amount:.0f} грн\n"
            f"💎 Итого: <b>{total:.0f} грн</b>\n\n"
            f"📌 Команда для зачисления:\n"
            f"<code>/pay {message.from_user.id} {total:.0f}</code>"
        )
        
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Чек отправлен!</b>\n\n"
            f"💰 Сумма к зачислению: {total:.0f} грн\n\n"
            f"⏱ Ожидайте зачисления средств",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        await state.clear()

    @dp.message(PaymentStates.waiting_deposit_card_proof)
    async def invalid_deposit_card_proof(message: types.Message):
        await message.answer(
            "❌ <b>Отправьте скриншот!</b>\n\n"
            "Фото + сумма в подписи\n"
            "<i>Пример: 500 грн</i>",
            parse_mode="HTML"
        )

    # ========== ОПЛАТА ЗАКАЗА С БАЛАНСА ==========
    
    @dp.callback_query(F.data == "pay_balance")
    async def pay_from_balance(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        user_id = callback.from_user.id
        balance, ref_id, total_spent, _ = await get_user(user_id)
        total_with_discount = data.get('final_amount', 0)
        test_mode = await get_config('test_mode') == 'True'
        
        if balance < total_with_discount and not test_mode:
            await callback.answer("❌ Недостаточно средств!", show_alert=True)
            return
        
        order_id = await add_order(
            user_id, data['link'], data.get('topic', '—'),
            data.get('geo'), data.get('sex'), data.get('age'), data.get('has_avatar'),
            data['count'], total_with_discount, 'pending'
        )
        
        if not test_mode:
            await update_balance(user_id, -total_with_discount)
        await update_user_stats(user_id, total_with_discount)
        
        if ref_id and not test_mode:
            ref_percent = float(await get_config('ref_percent') or 0.15)
            bonus = total_with_discount * ref_percent
            await update_balance(ref_id, bonus)
            try:
                await bot.send_message(ref_id, f"💰 Реферальный бонус +{bonus:.2f} грн!")
            except:
                pass
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Одобрить", callback_data=f"moder_approve_{order_id}"),
                    types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"moder_reject_{order_id}"))
        
        admin_text = (
            f"<b>🆕 ЗАКАЗ #{order_id}</b>\n\n"
            f"👤 Клиент: @{callback.from_user.username}\n"
            f"📎 Ссылка: {data['link']}\n"
            f"🎯 Тематика: {data.get('topic', '—')}\n"
            f"👥 Количество: {data['count']} шт\n"
            f"💰 Сумма: {total_with_discount:.2f} грн\n\n"
            f"🌍 {data.get('geo')} | 👤 {data.get('sex')} | 🎂 {data.get('age')} | 🖼️ {data.get('has_avatar')}"
        )
        
        admin_msg = await bot.send_message(ADMIN_ID, admin_text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await update_order_admin_msg(order_id, admin_msg.message_id)
        
        await callback.message.edit_text(
            f"✅ <b>Заказ #{order_id} оплачен!</b>\n\n"
            f"💰 Списано: {total_with_discount:.2f} грн\n\n"
            f"📋 Заказ отправлен на модерацию.",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        await state.clear()

    # ========== ОПЛАТА ЗАКАЗА USDT ==========
    
    @dp.callback_query(F.data == "pay_crypto")
    async def pay_crypto(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        total = data.get('final_amount', 0)
        usd_rate = float(await get_config('usd_to_uah') or USD_TO_UAH)
        amount_usdt = round(total / usd_rate, 2)
        
        order_id = await add_order(
            callback.from_user.id, data['link'], data.get('topic', '—'),
            data.get('geo'), data.get('sex'), data.get('age'), data.get('has_avatar'),
            data['count'], total, 'pending_payment'
        )
        
        await state.update_data(proof_order_id=order_id)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"crypto_paid_{order_id}"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="continue_to_price"))
        
        await callback.message.edit_text(
            f"🪙 <b>Оплата USDT</b>\n\n"
            f"💰 <b>Сумма:</b> {amount_usdt} USDT (~{total:.0f} грн)\n\n"
            f"<b>Наши кошельки:</b>\n"
            f"🔹 TRC-20: <code>{USDT_TRC20}</code>\n"
            f"🔹 BEP-20: <code>{USDT_BEP20}</code>\n"
            f"🔹 TON: <code>{USDT_TON}</code>\n\n"
            f"📌 Переведите сумму и нажмите «Я оплатил»",
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )

    @dp.callback_query(F.data.startswith("crypto_paid_"))
    async def crypto_paid(callback: types.CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[2])
        await callback.message.edit_text(
            "📸 <b>Отправьте чек оплаты</b>\n\n"
            "В подписи укажите сумму в USDT\n"
            "<i>Пример: 50 USDT TRC-20</i>",
            reply_markup=back_kb("continue_to_price"), parse_mode="HTML"
        )
        await state.update_data(proof_order_id=order_id)
        await state.set_state(PaymentStates.waiting_crypto_proof)

    @dp.message(PaymentStates.waiting_crypto_proof, F.photo)
    async def process_crypto_proof(message: types.Message, state: FSMContext):
        data = await state.get_data()
        order_id = data.get('proof_order_id')
        
        if not order_id:
            await message.answer("❌ Ошибка! Начните оплату заново.")
            await state.clear()
            return
        
        order = await get_order(order_id)
        if not order:
            await message.answer("❌ Заказ не найден!")
            await state.clear()
            return
        
        photo_id = message.photo[-1].file_id
        await update_order_proof(order_id, photo_id)
        
        admin_text = (
            f"<b>🆕 ЗАКАЗ #{order_id} (оплата USDT)</b>\n\n"
            f"👤 Клиент: @{message.from_user.username}\n"
            f"📎 Ссылка: {order[2]}\n"
            f"🎯 Тематика: {order[3]}\n"
            f"👥 Количество: {order[8]} шт\n"
            f"💰 Сумма: {order[9]:.0f} грн\n\n"
            f"📌 Выберите действие:"
        )
        
        await bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, reply_markup=moderation_kb(order_id), parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Чек отправлен!</b>\n\n"
            f"📋 Заказ #{order_id} отправлен на проверку.",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        await state.clear()

    # ========== ОПЛАТА ЗАКАЗА КАРТОЙ ==========
    
    @dp.callback_query(F.data == "pay_card")
    async def pay_card(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        total = data.get('final_amount', 0)
        
        order_id = await add_order(
            callback.from_user.id, data['link'], data.get('topic', '—'),
            data.get('geo'), data.get('sex'), data.get('age'), data.get('has_avatar'),
            data['count'], total, 'pending_payment'
        )
        
        await state.update_data(proof_order_id=order_id)
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"card_paid_{order_id}"))
        builder.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data="continue_to_price"))
        
        await callback.message.edit_text(
            f"💳 <b>Оплата картой</b>\n\n"
            f"💰 <b>Сумма:</b> {total:.0f} грн\n\n"
            f"<b>Реквизиты:</b>\n"
            f"<code>{CARD_NUMBER}</code>\n\n"
            f"📌 Переведите сумму и нажмите «Я оплатил»\n\n"
            f"⏱ Зачисление: 1-30 минут",
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )

    @dp.callback_query(F.data.startswith("card_paid_"))
    async def card_paid(callback: types.CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[2])
        await callback.message.edit_text(
            "📸 <b>Отправьте чек оплаты</b>\n\n"
            "В подписи укажите сумму в грн\n"
            "<i>Пример: 500 грн</i>",
            reply_markup=back_kb("continue_to_price"), parse_mode="HTML"
        )
        await state.update_data(proof_order_id=order_id)
        await state.set_state(PaymentStates.waiting_card_proof)

    @dp.message(PaymentStates.waiting_card_proof, F.photo)
    async def process_card_proof(message: types.Message, state: FSMContext):
        data = await state.get_data()
        order_id = data.get('proof_order_id')
        
        if not order_id:
            await message.answer("❌ Ошибка! Начните оплату заново.")
            await state.clear()
            return
        
        order = await get_order(order_id)
        if not order:
            await message.answer("❌ Заказ не найден!")
            await state.clear()
            return
        
        photo_id = message.photo[-1].file_id
        await update_order_proof(order_id, photo_id)
        
        admin_text = (
            f"<b>🆕 ЗАКАЗ #{order_id} (оплата картой)</b>\n\n"
            f"👤 Клиент: @{message.from_user.username}\n"
            f"📎 Ссылка: {order[2]}\n"
            f"🎯 Тематика: {order[3]}\n"
            f"👥 Количество: {order[8]} шт\n"
            f"💰 Сумма: {order[9]:.0f} грн\n\n"
            f"📌 Выберите действие:"
        )
        
        await bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, reply_markup=moderation_kb(order_id), parse_mode="HTML")
        
        await message.answer(
            f"✅ <b>Чек отправлен!</b>\n\n"
            f"📋 Заказ #{order_id} отправлен на проверку.",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )
        await state.clear()