import os
import requests
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("--- Инициализация бота ---")
print("SUPABASE_URL:", SUPABASE_URL if SUPABASE_URL else "НЕ ЗАДАН В .ENV!")
print("SUPABASE_KEY задан:", bool(SUPABASE_KEY))
print("BOT_TOKEN задан:", bool(BOT_TOKEN))

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

user_sessions = {}

def get_employees():
    url = f"{SUPABASE_URL}/rest/v1/employees?select=id,full_name,department,role,mentor_name&order=id.desc&limit=8"
    print(f"Запрос к Supabase: GET {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        print(f"Ответ Supabase: статус {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Успешно получено сотрудников: {len(data)}")
            return data
        else:
            print(f"Ошибка ответа Supabase (код {r.status_code}): {r.text}")
            return []
    except Exception as e:
        print("Исключение при запросе к Supabase:", e)
        return []

def save_pulse(emp_id, lunch_ok, mentor_helped, tasks_clear, sos_signal, comment, risk_level):
    url = f"{SUPABASE_URL}/rest/v1/pulse_checks"
    payload = {
        "employee_id": emp_id,
        "lunch_ok": lunch_ok,
        "mentor_helped": mentor_helped,
        "tasks_clear": tasks_clear,
        "sos_signal": sos_signal,
        "comment": comment,
        "risk_level": risk_level
    }
    print(f"Сохранение пульса: POST {url} (emp_id={emp_id}, risk={risk_level})")
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        print(f"Ответ сохранения пульса: статус {r.status_code}")
    except Exception as e:
        print("Ошибка сохранения пульса:", e)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    print(f"Получена команда /start от пользователя {message.from_user.id}")
    employees = get_employees()
    markup = types.InlineKeyboardMarkup()
    for emp in employees:
        markup.add(types.InlineKeyboardButton(
            text=f"👤 {emp['full_name']} ({emp['department']})",
            callback_data=f"emp_{emp['id']}"
        ))

    bot.send_message(
        message.chat.id,
        "👋 **Добро пожаловать в команду «СпортТовары»!**\n\n"
        "Я твой цифровой напарник на время испытательного срока.\n"
        "Помогу не потеряться, подскажу главное и вовремя помогу, если возникли трудности.\n\n"
        "👇 **Выбери себя из списка новичков:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("emp_"))
def select_emp(call):
    emp_id = int(call.data.split("_")[1])
    user_sessions[call.from_user.id] = {"emp_id": emp_id}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Памятка на смену", callback_data="memo"))
    markup.add(types.InlineKeyboardButton("📊 Пройти пульс дня (15 сек)", callback_data="q_lunch"))
    markup.add(types.InlineKeyboardButton("🆘 Мне нужна помощь (SOS)", callback_data="sos"))

    bot.edit_message_text(
        "✅ Отлично, профиль выбран!\nЧем могу помочь сегодня?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "memo")
def show_memo(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="menu"))
    bot.edit_message_text(
        "📋 **Главное на смене:**\n\n"
        "1. **Форма и шкафчик:** Раздевалка на 2 этаже, ключ у старшего смены.\n"
        "2. **Обед:** 45 минут в интервале 13:00–15:00. В столовой есть чай и микроволновки.\n"
        "3. **Инструменты:** Сканеры ТСД и рации сдаются в конце смены под роспись.\n"
        "4. **Любой вопрос:** Не стесняйся спрашивать наставника — глупых вопросов нет!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "q_lunch")
def question_lunch(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, всё вовремя", callback_data="lunch_1"))
    markup.add(types.InlineKeyboardButton("❌ Нет, не успел / не отпустили", callback_data="lunch_0"))
    bot.edit_message_text(
        "🍽 **Вопрос 1 из 3:**\n\nУспел ли ты сегодня нормально пообедать и отдохнуть?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lunch_"))
def question_mentor(call):
    val = (call.data == "lunch_1")
    user_sessions.setdefault(call.from_user.id, {})["lunch_ok"] = val

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, помог и объяснил", callback_data="mentor_1"))
    markup.add(types.InlineKeyboardButton("❌ Нет, был занят / остался один", callback_data="mentor_0"))
    bot.edit_message_text(
        "🤝 **Вопрос 2 из 3:**\n\nЕсли возникали затыки в работе, наставник помог тебе?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("mentor_"))
def question_tasks(call):
    val = (call.data == "mentor_1")
    user_sessions.setdefault(call.from_user.id, {})["mentor_helped"] = val

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, всё понятно", callback_data="tasks_1"))
    markup.add(types.InlineKeyboardButton("⚠️ Есть сомнения / не до конца", callback_data="tasks_0"))
    bot.edit_message_text(
        "🎯 **Вопрос 3 из 3:**\n\nПонятно ли, какие задачи стоят перед тобой на завтра?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tasks_"))
def finish_pulse(call):
    val = (call.data == "tasks_1")
    uid = call.from_user.id
    session = user_sessions.setdefault(uid, {})
    session["tasks_clear"] = val

    emp_id = session.get("emp_id", 1)
    lunch_ok = session.get("lunch_ok", True)
    mentor_helped = session.get("mentor_helped", True)
    tasks_clear = val

    if not lunch_ok or not mentor_helped:
        risk_level = "RED"
        comment = "Скрытый стресс: пропуск обеда или наставник не помог"
    elif not tasks_clear:
        risk_level = "YELLOW"
        comment = "Непонимание задач на завтра"
    else:
        risk_level = "GREEN"
        comment = "Смена прошла продуктивно"

    save_pulse(emp_id, lunch_ok, mentor_helped, tasks_clear, False, comment, risk_level)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="menu"))
    bot.edit_message_text(
        "🙌 **Спасибо за честные ответы!**\n\n"
        "Они помогают нам вовремя увидеть проблемы и сделать твои смены комфортнее. Хорошего отдыха!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "sos")
def trigger_sos(call):
    uid = call.from_user.id
    emp_id = user_sessions.get(uid, {}).get("emp_id", 1)

    save_pulse(emp_id, False, False, False, True, "Сотрудник запросил помощь через SOS", "RED")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="menu"))
    bot.edit_message_text(
        "🚨 **Сигнал тревоги принят!**\n\n"
        "Мы передали информацию руководителю адаптации. С тобой свяжутся в ближайшее время.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "menu")
def back_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Памятка на смену", callback_data="memo"))
    markup.add(types.InlineKeyboardButton("📊 Пройти пульс дня (15 сек)", callback_data="q_lunch"))
    markup.add(types.InlineKeyboardButton("🆘 Мне нужна помощь (SOS)", callback_data="sos"))
    bot.edit_message_text("Главное меню напарника:", call.message.chat.id, call.message.message_id, reply_markup=markup)

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
