# database.py
import asyncpg
import os
from datetime import datetime

# Данные для подключения к PostgreSQL из переменных окружения
DB_CONFIG = {
    'host': 'node1.pghost.ru',
    'port': 15641,
    'database': 'bothost_db_cda05fc8ae5d',
    'user': 'bothost_db_cda05fc8ae5d',
    'password': 'p3BNivG9t1w1kSrK_bTglRhc5qfzAsLSPCGnWNgjVc0'
}

# Глобальный пул соединений
db_pool = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(**DB_CONFIG)
    
    async with db_pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                referrer_id BIGINT,
                total_spent REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                registration_date TEXT,
                last_activity TEXT
            )
        ''')
        
        # Таблица заказов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                user_id BIGINT,
                link TEXT,
                topic TEXT,
                geo TEXT,
                sex TEXT,
                age TEXT,
                has_avatar TEXT,
                count INTEGER,
                amount REAL,
                status TEXT,
                date TEXT,
                moderated_at TEXT,
                moderated_by BIGINT,
                admin_msg_id BIGINT,
                proof_photo_id TEXT
            )
        ''')
        
        # Таблица конфигов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Таблица заблокированных
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_users (
                user_id BIGINT PRIMARY KEY
            )
        ''')
        
        # Настройки по умолчанию
        defaults = {
            'test_mode': 'False',
            'usd_to_uah': '41.0',
            'base_price': '2.0',
            'filter_surcharge': '0.5',
            'ref_percent': '0.15',
        }
        for key, value in defaults.items():
            await conn.execute('''
                INSERT INTO config (key, value, updated_at) 
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO NOTHING
            ''', key, value, datetime.now().isoformat())
    
    print("✅ PostgreSQL база данных готова")

async def get_user(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT balance, referrer_id, total_spent, total_orders FROM users WHERE user_id = $1', user_id)
        if row:
            return (row['balance'], row['referrer_id'], row['total_spent'], row['total_orders'])
        return (0, None, 0, 0)

async def get_user_info(user_id):
    """Полная информация о пользователе для админки"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT user_id, username, balance, total_spent, total_orders, 
                   referrer_id, registration_date, last_activity 
            FROM users WHERE user_id = $1
        ''', user_id)
        return row

async def update_balance(user_id, amount):
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', amount, user_id)

async def set_balance(user_id, amount):
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE users SET balance = $1 WHERE user_id = $2', amount, user_id)

async def update_user_stats(user_id, amount_spent):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE users 
            SET total_spent = total_spent + $1, 
                total_orders = total_orders + 1, 
                last_activity = $2 
            WHERE user_id = $3
        ''', amount_spent, datetime.now().isoformat(), user_id)

async def add_order(user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, admin_msg_id=None, proof_photo_id=None):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('''
            INSERT INTO orders (user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, date, admin_msg_id, proof_photo_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING order_id
        ''', user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, datetime.now().isoformat(), admin_msg_id, proof_photo_id)
        return row['order_id']

async def update_order_status(order_id, status, admin_id=None):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE orders SET status = $1, moderated_at = $2, moderated_by = $3 WHERE order_id = $4
        ''', status, datetime.now().isoformat(), admin_id, order_id)

async def update_order_proof(order_id, photo_id):
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE orders SET proof_photo_id = $1 WHERE order_id = $2', photo_id, order_id)

async def update_order_admin_msg(order_id, admin_msg_id):
    async with db_pool.acquire() as conn:
        await conn.execute('UPDATE orders SET admin_msg_id = $1 WHERE order_id = $2', admin_msg_id, order_id)

async def get_order(order_id):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow('SELECT * FROM orders WHERE order_id = $1', order_id)

async def get_user_orders(user_id):
    async with db_pool.acquire() as conn:
        return await conn.fetch('''
            SELECT order_id, link, topic, count, amount, status, date 
            FROM orders WHERE user_id = $1 ORDER BY date DESC LIMIT 10
        ''', user_id)

async def get_order_stats(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT COUNT(*), COALESCE(SUM(amount), 0) 
            FROM orders WHERE user_id = $1 AND status IN ('approved', 'completed')
        ''', user_id)
        return (row[0], row[1]) if row else (0, 0)

async def get_config(key):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT value FROM config WHERE key = $1', key)
        return row['value'] if row else None

async def set_config(key, value):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE config SET value = $1, updated_at = $2 WHERE key = $3
        ''', str(value), datetime.now().isoformat(), key)

async def is_blocked(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT user_id FROM blocked_users WHERE user_id = $1', user_id)
        return row is not None

async def block_user(user_id, blocked=True):
    async with db_pool.acquire() as conn:
        if blocked:
            await conn.execute('INSERT INTO blocked_users (user_id) VALUES ($1) ON CONFLICT DO NOTHING', user_id)
        else:
            await conn.execute('DELETE FROM blocked_users WHERE user_id = $1', user_id)

async def get_all_users():
    async with db_pool.acquire() as conn:
        return await conn.fetch('''
            SELECT user_id, username, balance, total_spent, total_orders, registration_date 
            FROM users ORDER BY total_spent DESC
        ''')

async def get_stats():
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
        total_orders = await conn.fetchval('SELECT COUNT(*) FROM orders')
        total_volume = await conn.fetchval('SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status IN ($1, $2)', 'approved', 'completed')
        avg_order = await conn.fetchval('SELECT COALESCE(AVG(amount), 0) FROM orders WHERE status IN ($1, $2)', 'approved', 'completed')
        pending_orders = await conn.fetchval('SELECT COUNT(*) FROM orders WHERE status = $1', 'pending')
        return total_users, total_orders, total_volume, avg_order, pending_orders