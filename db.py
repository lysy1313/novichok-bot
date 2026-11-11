import requests
from config import SUPABASE_URL, HEADERS

def get_employees():
    url = f"{SUPABASE_URL}/rest/v1/employees?select=id,full_name,department,role,mentor_name&order=id.desc&limit=8"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print("Ошибка получения сотрудников:", e)
        return []

def link_telegram_id(emp_id, telegram_id):
    url = f"{SUPABASE_URL}/rest/v1/employees?id=eq.{emp_id}"
    try:
        requests.patch(url, headers=HEADERS, json={"telegram_id": telegram_id}, timeout=5)
        print(f"Привязан telegram_id {telegram_id} к сотруднику {emp_id}")
    except Exception as e:
        print("Ошибка привязки telegram_id:", e)

def get_employee_tasks(emp_id):
    url = f"{SUPABASE_URL}/rest/v1/employee_tasks?employee_id=eq.{emp_id}&order=id.asc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print("Ошибка получения задач:", e)
        return []

def toggle_task(task_id, current_status):
    url = f"{SUPABASE_URL}/rest/v1/employee_tasks?id=eq.{task_id}"
    try:
        requests.patch(url, headers=HEADERS, json={"is_completed": not current_status}, timeout=5)
    except Exception as e:
        print("Ошибка переключения задачи:", e)

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
    try:
        requests.post(url, headers=HEADERS, json=payload, timeout=5)
    except Exception as e:
        print("Ошибка сохранения пульса:", e)
