import telebot
from telebot import types
import edge_tts
import asyncio
import os
import sqlite3
import random
from flask import Flask
from threading import Thread

# --- ТАНЗИМОТ ---
TOKEN = '8073303487:AAE5YzxhAGzDaTPHE8p1Sj-7NBN67fOmLe4'
ADMIN_ID = 8014656470
bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Бот фаъол аст!"

def run_web(): app.run(host='0.0.0.0', port=8080)

# Базаи маълумот
conn = sqlite3.connect('mega.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, voice TEXT)')

# Овозҳо
VOICES = {
    "👩 Саломат": "tg-TJ-SalomatNeural",
    "👨 Витоли": "tg-TJ-VitoliNeural",
    "🇷🇺 Дмитрий": "ru-RU-DmitryNeural"
}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("🎤 Овозҳо", "🖼 QR-Код", "🔐 Парол")
    markup.add("🎲 Бозӣ", "💡 Маслиҳат", "📜 Иқтибос")
    markup.add("🆔 ID-и ман", "👨‍💻 Админ", "📊 Стат")
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', (m.chat.id, VOICES["👩 Саломат"]))
    bot.send_message(m.chat.id, "Хуш омадед ба Mega-Voice Bot! 🚀", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎤 Овозҳо")
def voice_sel(m):
    markup = types.InlineKeyboardMarkup()
    for name, v in VOICES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=v))
    bot.send_message(m.chat.id, "Овозро интихоб кунед:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    conn.execute('UPDATE users SET voice = ? WHERE id = ?', (call.data, call.message.chat.id))
    bot.answer_callback_query(call.id, "Овоз иваз шуд! ✅")

@bot.message_handler(func=lambda m: m.text == "🖼 QR-Код")
def qr(m):
    msg = bot.send_message(m.chat.id, "Текстро фиристед:")
    bot.register_next_step_handler(msg, lambda ms: bot.send_photo(ms.chat.id, f"https://api.qrserver.com/v1/create-qr-code/?data={ms.text}"))

@bot.message_handler(func=lambda m: m.text == "🔐 Парол")
def passgen(m):
    p = "".join(random.sample("abcdefgh12345678!@#$", 10))
    bot.send_message(m.chat.id, f"Пароли шумо: `{p}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📊 Стат" and m.chat.id == ADMIN_ID)
def stat(m):
    c = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    bot.send_message(ADMIN_ID, f"Обуначиён: {c}")

# Текст ба Овоз (Агар тугма набошад)
async def tts_save(text, voice, file):
    await edge_tts.Communicate(text, voice).save(file)

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    if m.text in ["🎤 Овозҳо", "🖼 QR-Код", "🔐 Парол", "🎲 Бозӣ", "💡 Маслиҳат", "📊 Стат"]: return
    user_voice = conn.execute('SELECT voice FROM users WHERE id = ?', (m.chat.id,)).fetchone()[0]
    path = f"v_{m.chat.id}.mp3"
    try:
        asyncio.run(tts_save(m.text, user_voice, path))
        with open(path, 'rb') as audio: bot.send_voice(m.chat.id, audio)
        os.remove(path)
    except Exception as e: bot.send_message(m.chat.id, f"Хатогӣ: {e}")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
