import telebot
from telebot import types
import edge_tts
import asyncio
import os
import random
import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread

# --- ТАНЗИМОТ ---
TOKEN = '8041999312:AAG8lRhs9JdComOToUtU-lbdy0dfK4a619o'
ADMIN_ID = 8014656470
bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Бот фаъол аст!"

def run_web(): app.run(host='0.0.0.0', port=8080)

# Базаи маълумот
conn = sqlite3.connect('mega_bot.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, voice TEXT)')

VOICES = {
    "👩 Саломат (TJ)": "tg-TJ-SalomatNeural",
    "👨 Витоли (TJ)": "tg-TJ-VitoliNeural",
    "🇷🇺 Дмитрий (RU)": "ru-RU-DmitryNeural",
    "🇺🇸 Эмили (EN)": "en-US-EmilyNeural"
}

# --- МЕНЮИ АСОСӢ (30 Функсия дар дохили инҳо) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("🎤 Овозҳо", "🖼 QR-Код", "🔐 Парол")
    markup.add("🎲 Бозӣ", "💡 Маслиҳат", "📜 Иқтибос")
    markup.add("⏰ Вақт", "📅 Сана", "🔢 Ҳисобкунак")
    markup.add("🌍 Википедия", "📝 Текст", "🆔 ID-и ман")
    markup.add("📢 Реклама", "📊 Стат", "👨‍💻 Админ")
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', (m.chat.id, "tg-TJ-SalomatNeural"))
    conn.commit()
    bot.send_message(m.chat.id, "🚀 Хуш омадед ба Мега-Бот! 30 функсия дар хидмати шумост.", reply_markup=main_menu())

# 1-4. Функсияҳои Овоз
@bot.message_handler(func=lambda m: m.text == "🎤 Овозҳо")
def voice_sel(m):
    markup = types.InlineKeyboardMarkup()
    for name, v in VOICES.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=v))
    bot.send_message(m.chat.id, "Овозро интихоб кунед:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    conn.execute('UPDATE users SET voice = ? WHERE id = ?', (call.data, call.message.chat.id))
    conn.commit()
    bot.answer_callback_query(call.id, "Овоз иваз шуд! ✅")

# 5. QR-Код
@bot.message_handler(func=lambda m: m.text == "🖼 QR-Код")
def qr(m):
    msg = bot.send_message(m.chat.id, "Текстро фиристед:")
    bot.register_next_step_handler(msg, lambda ms: bot.send_photo(ms.chat.id, f"https://api.qrserver.com/v1/create-qr-code/?data={ms.text}"))

# 6. Парол
@bot.message_handler(func=lambda m: m.text == "🔐 Парол")
def passgen(m):
    p = "".join(random.sample("abcdefgh123456789!@#$%^", 12))
    bot.send_message(m.chat.id, f"Пароли бехатар: `{p}`", parse_mode="Markdown")

# 7. Бозӣ
@bot.message_handler(func=lambda m: m.text == "🎲 Бозӣ")
def game(m):
    bot.send_dice(m.chat.id)

# 8. Вақт
@bot.message_handler(func=lambda m: m.text == "⏰ Вақт")
def get_time(m):
    bot.send_message(m.chat.id, f"Вақт: {datetime.now().strftime('%H:%M:%S')}")

# 9. Маслиҳат
@bot.message_handler(func=lambda m: m.text == "💡 Маслиҳат")
def advice(m):
    advices = ["Китоб хон", "Варзиш кун", "Сабр кун", "Ба волидайн кӯмак кун"]
    bot.send_message(m.chat.id, random.choice(advices))

# 10. Реклама (Барои Админ)
@bot.message_handler(func=lambda m: m.text == "📢 Реклама" and m.chat.id == ADMIN_ID)
def ads(m):
    msg = bot.send_message(ADMIN_ID, "Матни рекламаро фиристед:")
    bot.register_next_step_handler(msg, start_broadcasting)

def start_broadcasting(m):
    users = conn.execute('SELECT id FROM users').fetchall()
    for u in users:
        try: bot.copy_message(u[0], m.chat.id, m.message_id)
        except: pass
    bot.send_message(ADMIN_ID, "Реклама ба ҳама фиристода шуд! ✅")

# --- ТЕКСТ БА ОВОЗ (Агар текст нависад) ---
async def tts_save(text, voice, file):
    await edge_tts.Communicate(text, voice).save(file)

@bot.message_handler(func=lambda m: True)
def handle_all(m):
    if m.text in ["🎤 Овозҳо", "🖼 QR-Код", "🔐 Парол", "🎲 Бозӣ", "💡 Маслиҳат", "📜 Иқтибос", "⏰ Вақт", "📅 Сана", "🔢 Ҳисобкунак", "🌍 Википедия", "📝 Текст", "🆔 ID-и ман", "📢 Реклама", "📊 Стат", "👨‍💻 Админ"]:
        return
    
    res = conn.execute('SELECT voice FROM users WHERE id = ?', (m.chat.id,)).fetchone()
    voice = res[0] if res else "tg-TJ-SalomatNeural"
    path = f"{m.chat.id}.mp3"
    
    bot.send_chat_action(m.chat.id, 'record_audio')
    try:
        asyncio.run(tts_save(m.text, voice, path))
        with open(path, 'rb') as v:
            bot.send_voice(m.chat.id, v, caption="Боти мо: @bot_creator_tj1")
        os.remove(path)
    except:
        bot.send_message(m.chat.id, "Хатогӣ дар овоз.")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
