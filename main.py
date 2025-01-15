import requests
import json
from datetime import datetime, timezone
import telebot
import time

API_URL = 'https://pravburo.moizvonki.ru/api/v1'
API_KEY = 'mi7phnkxrpt0e46xvrp6dlkykhj8j9sm'

managers = ['pravburo108@gmail.com', 'pravburo102@gmail.com', 'pravburo107@gmail.com', 'pravburo115@gmail.com', 'pravburo119@gmail.com']


manager_keys = {
    "m13": "pravburo108@gmail.com",
    "m12": "pravburo102@gmail.com",
    "m21": "pravburo107@gmail.com",
    "m20": "pravburo115@gmail.com",
    "m99": 'pravburo119@gmail.com',
}

manager_names = {
    'pravburo108@gmail.com': 'Александра',
    'pravburo102@gmail.com': 'Витя',
    'pravburo107@gmail.com': 'Света',
    'pravburo115@gmail.com': 'Миша',
    'pravburo119@gmail.com': 'Наташа'
}

bot = telebot.TeleBot("7206769028:AAGk2mOX2sjSn_tMkVIEWNkFVRDvuuTNYcU")
chat_id = -4667960936

manager_data = {}

MANAGER_ORDER = [
    'pravburo108@gmail.com',
    'pravburo102@gmail.com',
    'pravburo107@gmail.com',
    'pravburo115@gmail.com',
    'pravburo119@gmail.com'
]

key_dict = {
    "count": "Мои звонки(Количество)",
    "duration": "Мои звонки(Время)",
    "danger": "Мои звонки(Недозвоны)",
    "W_duration": "Мессенджеры(Количество звонков)",
    "W_count": "Мессенджеры(Количество чатов)",
}

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def get_all_calls(username, from_date, to_date):
    offset = 0
    all_calls = []

    while True:
        request_data = {
            "user_name": username,
            "api_key": API_KEY,
            "action": "calls.list",
            "from_date": from_date,
            "to_date": to_date,
            "max_results": 100,
            "from_offset": offset,
            "supervised": 0
        }

        response = requests.post(API_URL, data=json.dumps(request_data), headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            try:
                data = response.json()
                calls = data.get('results', [])
                if not calls:
                    break  
                all_calls.extend(calls)
                offset += len(calls)  
            except ValueError as e:
                print(f"Ошибка при разборе JSON для менеджера {username}:", e)
                break
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            break

    return all_calls



@bot.message_handler(commands=['refresh'])
def handle_refresh_commands(message):
    url = 'https://prav-buro.ru/changes/6/'
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json() 

        if "changes_count" in data:
            manager_data["pravburo119@gmail.com"]["lk"] = data["changes_count"]
            bot.send_message(chat_id, "Успешный запрос! Изменения в ЛК обновлены.")
        else:
            bot.send_message(chat_id, "Некорректный ответ сервера. Нет ключа 'changes_count'.")
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"Ошибка запроса: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        
        
@bot.message_handler(commands=['process'])
def handle_process_command(message):
    bot.send_message(chat_id, "Делаю запрос к API")
    try:
        today = datetime.today()
        start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc)
        end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)

        from_date = int(start_of_day.timestamp())
        to_date = int(end_of_day.timestamp())

        for manager_email in MANAGER_ORDER:
            username = manager_email
            if username:
                calls = get_all_calls(username, from_date, to_date)

                if username not in manager_data:
                    manager_data[username] = {
                        'count': 0,
                        'duration': '00:00:00',
                        'danger': 0,
                        'W_duration': 0,
                        'W_count': 0
                    }

                total_duration = 0
                count_today = 0
                count_danger = 0

                for call in calls:
                    answered = call.get('answered', 0)
                    duration = call.get('duration', 0)

                    count_today += 1
                    if answered == 0:
                        count_danger += 1
                    total_duration += duration

                manager_data[username]['count'] = count_today
                manager_data[username]['danger'] = count_danger
                manager_data[username]['duration'] = seconds_to_hms(total_duration)

        result_message = make_text(manager_data)
        bot.send_message(chat_id, result_message)

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при запросе: {e}")


def make_text(data):
    current_date = datetime.now().strftime("%d.%m.%Y")
    final_message = [f"Отчет {current_date}"]

    for manager_key in MANAGER_ORDER:
        if manager_key in data:
            final_message.append("\n")
            final_message.append(manager_names.get(manager_key, manager_key))  
            for key in key_dict:
                final_message.append(f"{key_dict[key]}: {data[manager_key].get(key, '0')}")

            if "lk" in data[manager_key]:
                final_message.append(f"Изменений в ЛК: {data[manager_key].get('lk', '0')}")

    return "\n".join(final_message)


@bot.message_handler(commands=['report'])
def handle_set_command(message):
    try:
        text = make_text(manager_data)
        bot.send_message(chat_id, text)
    except:
        bot.send_message(chat_id, "Что-то пошло не так с отправкой сообщения")



@bot.message_handler(commands=['set'])
def handle_set_command(message):
    try:
        command = message.text.split()
        if len(command) != 4:
            bot.send_message(chat_id, "Неверный формат команды. Пример: /set m13 120 5")
            return

        manager_key = command[1]
        w_duration = int(command[2]) 
        w_count = int(command[3])

        if manager_key not in manager_keys:
            bot.send_message(chat_id, f"Менеджер с ключом {manager_key} не найден.")
            return

        email = manager_keys[manager_key]

        if email not in manager_data:
            manager_data[email] = {
                'count': 0,
                'duration': '00:00:00',
                'danger': 0,
                'W_duration': 0,
                'W_count': 0
            }

        manager_data[email]['W_duration'] = w_duration
        manager_data[email]['W_count'] = w_count

        bot.send_message(chat_id, f"Данные для {manager_names[email]} обновлены")

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при обработке команды: {e}")
        
        
        

def start_bot():
    while True:
        try:
            bot.send_message(chat_id, "Бот запущен.")
            bot.polling(none_stop=True, interval=0)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_bot()
