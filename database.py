# database.py
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        referrer_id INTEGER,
        total_spent REAL DEFAULT 0,
        total_orders INTEGER DEFAULT 0,
        registration_date TEXT,
        last_activity TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
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
        moderated_by INTEGER,
        admin_msg_id INTEGER,
        proof_photo_id TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS blocked_users (
        user_id INTEGER PRIMARY KEY
    )''')
    
    defaults = {
        'test_mode': 'False',
        'usd_to_uah': '41.0',
        'base_price': '2.0',
        'filter_surcharge': '0.5',
        'ref_percent': '0.15',
    }
    for key, value in defaults.items():
        cursor.execute('INSERT OR IGNORE INTO config (key, value, updated_at) VALUES (?, ?, ?)',
                       (key, value, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print("✅ База данных готова")

def get_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, referrer_id, total_spent, total_orders FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, None, 0, 0)

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

def update_user_stats(user_id, amount_spent):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET total_spent = total_spent + ?, total_orders = total_orders + 1, last_activity = ? WHERE user_id = ?',
                   (amount_spent, datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def add_order(user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, admin_msg_id=None, proof_photo_id=None):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO orders (user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, date, admin_msg_id, proof_photo_id)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (user_id, link, topic, geo, sex, age, has_avatar, count, amount, status, datetime.now().isoformat(), admin_msg_id, proof_photo_id))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status, admin_id=None):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE orders SET status = ?, moderated_at = ?, moderated_by = ? WHERE order_id = ?''',
                   (status, datetime.now().isoformat(), admin_id, order_id))
    conn.commit()
    conn.close()

def update_order_proof(order_id, photo_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET proof_photo_id = ? WHERE order_id = ?', (photo_id, order_id))
    conn.commit()
    conn.close()

def update_order_admin_msg(order_id, admin_msg_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET admin_msg_id = ? WHERE order_id = ?', (admin_msg_id, order_id))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_pending_order(user_id):
    """Получает последний заказ пользователя со статусом pending_payment"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM orders WHERE user_id = ? AND status = 'pending_payment' ORDER BY order_id DESC LIMIT 1''', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_user_orders(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT order_id, link, topic, count, amount, status, date 
                      FROM orders WHERE user_id = ? ORDER BY date DESC LIMIT 10''', (user_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_order_stats(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM orders WHERE user_id = ? AND status IN ("approved", "completed")', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res or (0, 0)

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

def is_blocked(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM blocked_users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def block_user(user_id, blocked=True):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    if blocked:
        cursor.execute('INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)', (user_id,))
    else:
        cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, balance, total_spent, total_orders, registration_date FROM users ORDER BY total_spent DESC')
    res = cursor.fetchall()
    conn.close()
    return res

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

init_db()