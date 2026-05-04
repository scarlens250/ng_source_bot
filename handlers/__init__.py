# handlers/__init__.py
from handlers.user import register_user_handlers
from handlers.order import register_order_handlers
from handlers.payment import register_payment_handlers
from handlers.moderation import register_moderation_handlers

def register_handlers(dp, bot):
    register_user_handlers(dp, bot)
    register_order_handlers(dp)
    register_payment_handlers(dp, bot)
    register_moderation_handlers(dp, bot)