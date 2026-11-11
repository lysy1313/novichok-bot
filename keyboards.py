from telebot import types

def build_main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Задачи на смену", callback_data="tasks_menu"))
    markup.add(types.InlineKeyboardButton("📊 Пройти пульс дня (15 сек)", callback_data="q_lunch"))
    markup.add(types.InlineKeyboardButton("📋 Памятка на смену", callback_data="memo"))
    markup.add(types.InlineKeyboardButton("🆘 Мне нужна помощь (SOS)", callback_data="sos"))
    return markup

def build_employees_menu(employees):
    markup = types.InlineKeyboardMarkup()
    for emp in employees:
        markup.add(types.InlineKeyboardButton(
            text=f"👤 {emp['full_name']} ({emp['department']})",
            callback_data=f"emp_{emp['id']}"
        ))
    return markup

def build_tasks_menu(tasks):
    markup = types.InlineKeyboardMarkup()
    if tasks:
        for t in tasks:
            status_icon = "✅" if t["is_completed"] else "⬜"
            markup.add(types.InlineKeyboardButton(
                text=f"{status_icon} {t['title']}",
                callback_data=f"toggle_{t['id']}_{t['is_completed']}"
            ))
    markup.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="menu"))
    return markup

def build_lunch_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, всё вовремя", callback_data="lunch_1"))
    markup.add(types.InlineKeyboardButton("❌ Нет, не успел / не отпустили", callback_data="lunch_0"))
    return markup

def build_mentor_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, помог и объяснил", callback_data="mentor_1"))
    markup.add(types.InlineKeyboardButton("❌ Нет, был занят / остался один", callback_data="mentor_0"))
    return markup

def build_tasks_clear_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да, всё понятно", callback_data="tasks_1"))
    markup.add(types.InlineKeyboardButton("⚠️ Есть сомнения / не до конца", callback_data="tasks_0"))
    return markup

def build_comment_prompt_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ Написать комментарий", callback_data="comment_prompt"))
    markup.add(types.InlineKeyboardButton("Пропустить и отправить ➡️", callback_data="finish_no_comment"))
    return markup

def build_back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="menu"))
    return markup
