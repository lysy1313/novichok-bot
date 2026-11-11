import telebot
from config import BOT_TOKEN
import db
import keyboards

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    employees = db.get_employees()
    markup = keyboards.build_employees_menu(employees)
    bot.send_message(
        message.chat.id,
        "👋 **Добро пожаловать в команду «СпортТовары»!**\n\n"
        "Я твой цифровой напарник на время испытательного срока.\n"
        "Помогу сориентироваться, отмечать задачи смены и вовремя помогу при трудностях.\n\n"
        "👇 **Выбери себя из списка новичков:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("emp_"))
def select_emp(call):
    emp_id = int(call.data.split("_")[1])
    user_sessions[call.from_user.id] = {"emp_id": emp_id}
    db.link_telegram_id(emp_id, call.from_user.id)

    bot.edit_message_text(
        "✅ **Профиль выбран!**\nЧем займёмся сегодня?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_main_menu(),
        parse_mode="Markdown"
    )

# --- 1. ЗАДАЧИ НА СМЕНУ ---
@bot.callback_query_handler(func=lambda call: call.data == "tasks_menu")
def show_tasks_menu(call):
    emp_id = user_sessions.get(call.from_user.id, {}).get("emp_id", 1)
    tasks = db.get_employee_tasks(emp_id)
    markup = keyboards.build_tasks_menu(tasks)

    if not tasks:
        text = "📝 **Задачи на смену:**\n\nНаставник ещё не добавил задачи на сегодня. Скоро они появятся здесь!"
    else:
        text = "📝 **Твой чеклист задач от наставника:**\n\n*(Нажми на задачу, чтобы отметить её выполненной)*"

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_"))
def handle_toggle_task(call):
    parts = call.data.split("_")
    task_id = int(parts[1])
    current_status = (parts[2].lower() == 'true')
    db.toggle_task(task_id, current_status)
    show_tasks_menu(call)

# --- 2. ПАМЯТКА ---
@bot.callback_query_handler(func=lambda call: call.data == "memo")
def show_memo(call):
    bot.edit_message_text(
        "📋 **Главное на смене:**\n\n"
        "1. **Форма и шкафчик:** Раздевалка на 2 этаже, ключ у старшего смены.\n"
        "2. **Обед:** 45 минут в интервале 13:00–15:00. В столовой есть чай и микроволновки.\n"
        "3. **Инструменты:** Сканеры ТСД и рации сдаются в конце смены под роспись.\n"
        "4. **Любой вопрос:** Не стесняйся спрашивать наставника — глупых вопросов нет!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_back_menu(),
        parse_mode="Markdown"
    )

# --- 3. ПУЛЬС-ОПРОС ---
@bot.callback_query_handler(func=lambda call: call.data == "q_lunch")
def question_lunch(call):
    bot.edit_message_text(
        "🍽 **Вопрос 1 из 3:**\n\nУспел ли ты сегодня нормально пообедать и отдохнуть?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_lunch_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lunch_"))
def question_mentor(call):
    val = (call.data == "lunch_1")
    user_sessions.setdefault(call.from_user.id, {})["lunch_ok"] = val

    bot.edit_message_text(
        "🤝 **Вопрос 2 из 3:**\n\nЕсли возникали затыки в работе, наставник помог тебе?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_mentor_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("mentor_"))
def question_tasks(call):
    val = (call.data == "mentor_1")
    user_sessions.setdefault(call.from_user.id, {})["mentor_helped"] = val

    bot.edit_message_text(
        "🎯 **Вопрос 3 из 3:**\n\nПонятно ли, какие задачи стоят перед тобой на завтра?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_tasks_clear_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tasks_"))
def ask_comment(call):
    val = (call.data == "tasks_1")
    uid = call.from_user.id
    user_sessions.setdefault(uid, {})["tasks_clear"] = val

    bot.edit_message_text(
        "💬 **Почти готово!**\n\n"
        "Хочешь добавить что-то от себя своими словами или рассказать о проблеме?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_comment_prompt_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "comment_prompt")
def prompt_comment(call):
    user_sessions.setdefault(call.from_user.id, {})["state"] = "awaiting_comment_text"
    bot.edit_message_text(
        "✍️ **Напиши твой комментарий в чат:**\n*(мы сразу передадим его руководителю)*",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_back_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "finish_no_comment")
def finish_without_comment(call):
    save_session_pulse(call.from_user.id, custom_comment=None)
    bot.edit_message_text(
        "🙌 **Спасибо за честные ответы!**\n\n"
        "Они помогают нам делать твои смены комфортнее. Хорошего отдыха!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_back_menu(),
        parse_mode="Markdown"
    )

def save_session_pulse(uid, custom_comment=None):
    session = user_sessions.setdefault(uid, {})
    emp_id = session.get("emp_id", 1)
    lunch_ok = session.get("lunch_ok", True)
    mentor_helped = session.get("mentor_helped", True)
    tasks_clear = session.get("tasks_clear", True)

    if not lunch_ok or not mentor_helped:
        risk_level = "RED"
        default_comment = "Скрытый стресс: пропуск обеда или наставник не помог"
    elif not tasks_clear:
        risk_level = "YELLOW"
        default_comment = "Непонимание задач на завтра"
    else:
        risk_level = "GREEN"
        default_comment = "Смена прошла продуктивно"

    final_comment = custom_comment if custom_comment else default_comment
    db.save_pulse(emp_id, lunch_ok, mentor_helped, tasks_clear, False, final_comment, risk_level)
    session["state"] = None

# --- 4. ТЕКСТОВЫЕ КОММЕНТАРИИ ---
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    uid = message.from_user.id
    session = user_sessions.setdefault(uid, {})
    state = session.get("state")

    if state == "awaiting_comment_text":
        comment_text = message.text.strip()
        save_session_pulse(uid, custom_comment=comment_text)
        bot.send_message(
            message.chat.id,
            "🙌 **Комментарий принят и сохранён в дашборде!**\nСпасибо за обратную связь, хорошего отдыха!",
            reply_markup=keyboards.build_back_menu(),
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "Выбери действие в меню:", reply_markup=keyboards.build_main_menu())

# --- 5. SOS И МЕНЮ ---
@bot.callback_query_handler(func=lambda call: call.data == "sos")
def trigger_sos(call):
    uid = call.from_user.id
    emp_id = user_sessions.get(uid, {}).get("emp_id", 1)
    db.save_pulse(emp_id, False, False, False, True, "Сотрудник запросил помощь через кнопку SOS", "RED")

    bot.edit_message_text(
        "🚨 **Сигнал тревоги принят!**\n\n"
        "Мы передали информацию руководителю адаптации. С тобой свяжутся в ближайшее время.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_back_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "menu")
def back_menu(call):
    bot.edit_message_text(
        "Главное меню напарника:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.build_main_menu()
    )

if __name__ == "__main__":
    print("Бот запущен (модульная архитектура)...")
    bot.infinity_polling()
