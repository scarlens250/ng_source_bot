# handlers/moderation.py
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID
from database import get_order, update_order_status, update_balance, get_config, update_order_admin_msg

def register_moderation_handlers(dp: Dispatcher, bot: Bot):
    
    @dp.callback_query(F.data.startswith("moder_approve_"))
    async def moder_approve(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Только для админа!", show_alert=True)
            return
        
        order_id = int(callback.data.split("_")[2])
        order = await get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
        
        await update_order_status(order_id, "approved", ADMIN_ID)
        
        await bot.send_message(
            order[1],
            f"✅ <b>Заказ #{order_id} ОДОБРЕН!</b>\n\n"
            f"📊 Количество: {order[8]} подписчиков\n"
            f"💰 Сумма: {order[9]:.2f} грн\n\n"
            f"🔄 Статус: <b>В работе</b>",
            parse_mode="HTML"
        )
        
        complete_builder = InlineKeyboardBuilder()
        complete_builder.row(types.InlineKeyboardButton(text="🎉 Выполнено", callback_data=f"complete_{order_id}"))
        
        new_msg = await bot.send_message(
            ADMIN_ID,
            f"<b>✅ ЗАКАЗ #{order_id} ОДОБРЕН!</b>\n\n"
            f"👤 Клиент: @{callback.from_user.username}\n"
            f"📎 Ссылка: {order[2]}\n"
            f"🎯 Тематика: {order[3]}\n"
            f"👥 Количество: {order[8]} шт\n"
            f"💰 Сумма: {order[9]:.2f} грн\n\n"
            f"🌍 {order[4]} | 👤 {order[5]} | 🎂 {order[6]} | 🖼️ {order[7]}\n\n"
            f"<i>Когда налив будет сделан, нажмите «Выполнено»</i>",
            reply_markup=complete_builder.as_markup(),
            parse_mode="HTML"
        )
        
        await update_order_admin_msg(order_id, new_msg.message_id)
        
        if order[12]:
            try:
                old_builder = InlineKeyboardBuilder()
                old_builder.row(types.InlineKeyboardButton(text="✅ Одобрено", callback_data="done"))
                await bot.edit_message_reply_markup(
                    chat_id=ADMIN_ID,
                    message_id=order[12],
                    reply_markup=old_builder.as_markup()
                )
            except:
                pass
        
        await callback.answer("✅ Заказ одобрен!")

    @dp.callback_query(F.data.startswith("complete_"))
    async def complete_order(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Только для админа!", show_alert=True)
            return
        
        order_id = int(callback.data.split("_")[1])
        order = await get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
        
        await update_order_status(order_id, "completed", ADMIN_ID)
        
        await bot.send_message(
            order[1],
            f"🎉 <b>Заказ #{order_id} ВЫПОЛНЕН!</b>\n\n"
            f"📊 Количество: {order[8]} подписчиков\n"
            f"✅ Статус: <b>Завершён</b>\n\n"
            f"Спасибо!",
            parse_mode="HTML"
        )
        
        done_builder = InlineKeyboardBuilder()
        done_builder.row(types.InlineKeyboardButton(text="✅ Выполнено", callback_data="done"))
        
        try:
            await bot.edit_message_reply_markup(
                chat_id=ADMIN_ID,
                message_id=callback.message.message_id,
                reply_markup=done_builder.as_markup()
            )
        except:
            pass
        
        await callback.answer("🎉 Заказ выполнен!")

    @dp.callback_query(F.data.startswith("moder_reject_channel_"))
    async def moder_reject_channel(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Только для админа!", show_alert=True)
            return
        
        order_id = int(callback.data.split("_")[3])
        order = await get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
        
        test_mode = await get_config('test_mode') == 'True'
        await update_order_status(order_id, "rejected", ADMIN_ID)
        
        if not test_mode:
            await update_balance(order[1], order[9])
            money_text = f"💰 Деньги в сумме {order[9]:.2f} грн возвращены."
        else:
            money_text = "🧪 Тестовый режим."
        
        await bot.send_message(
            order[1],
            f"❌ <b>Заказ #{order_id} ОТКЛОНЁН!</b>\n\n"
            f"📝 Причина: канал не подходит.\n\n"
            f"{money_text}",
            parse_mode="HTML"
        )
        
        reject_builder = InlineKeyboardBuilder()
        reject_builder.row(types.InlineKeyboardButton(text="❌ Отклонено", callback_data="done"))
        
        try:
            await bot.edit_message_reply_markup(
                chat_id=ADMIN_ID,
                message_id=callback.message.message_id,
                reply_markup=reject_builder.as_markup()
            )
        except:
            pass
        
        await callback.answer("❌ Заказ отклонён!")

    @dp.callback_query(F.data.startswith("moder_reject_"))
    async def moder_reject(callback: types.CallbackQuery):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("⛔ Только для админа!", show_alert=True)
            return
        
        if "channel" in callback.data:
            return
        
        order_id = int(callback.data.split("_")[2])
        order = await get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
        
        await update_order_status(order_id, "rejected", ADMIN_ID)
        
        await bot.send_message(
            order[1],
            f"❌ <b>Заказ #{order_id} ОТКЛОНЁН!</b>\n\n"
            f"📝 Причина: оплата не подтверждена.",
            parse_mode="HTML"
        )
        
        reject_builder = InlineKeyboardBuilder()
        reject_builder.row(types.InlineKeyboardButton(text="❌ Отклонено", callback_data="done"))
        
        try:
            await bot.edit_message_reply_markup(
                chat_id=ADMIN_ID,
                message_id=callback.message.message_id,
                reply_markup=reject_builder.as_markup()
            )
        except:
            pass
        
        await callback.answer("❌ Заказ отклонён!")

    @dp.callback_query(F.data == "done")
    async def done_action(callback: types.CallbackQuery):
        await callback.answer("Уже выполнено", show_alert=True)