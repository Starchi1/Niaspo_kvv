import sqlite3
import telebot
from telebot import types
from datetime import datetime, timedelta
import os
# Создаем экземплярбота
bot = telebot.TeleBot("7588601604:AAFGdFd-_Gafzd2lZ94UFCl_5CYnb6gjw28")


ADMIN_ID = 1 # Замените на ID администратора
DB_PATH = os.getenv('DB_PATH', '/app/db/BD_kurs_clients.db')

# Функция для отправки главного меню
def send_main_menu(message, is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_admin:
        markup.add(types.KeyboardButton("Просмотреть всех клиентов"),
                   types.KeyboardButton("Просмотреть все заявки"),
                   types.KeyboardButton("Одобрить кредит по ID"),
                   types.KeyboardButton("Одобрить страховку по ID"),
                   types.KeyboardButton("Просмотреть пользователя по ID"))
    else:
        markup.add(types.KeyboardButton("Запросить услугу"),
                   types.KeyboardButton("Просмотреть мои услуги"),
                   types.KeyboardButton("Внести деньги на счёт"),)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


## Функция для админа: просмотр информации о клиенте по client_id
@bot.message_handler(func=lambda message: message.text == "Просмотреть пользователя по ID")
def prompt_for_client_id(message):
    bot.send_message(message.chat.id, "Введите ID клиента для просмотра информации:")
    bot.register_next_step_handler(message, view_client_by_id)


# Функция для вывода информации о конкретном клиенте по ID
def view_client_by_id(message):
    try:
        client_id = int(message.text)

        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            # Получаем данные о клиенте по конкретному ID
            cur.execute("SELECT ID, name, email, phone FROM clients WHERE ID = ?", (client_id,))
            client = cur.fetchone()

            if client:
                client_id, name, email, phone = client

                # Рассчитываем баланс клиента, суммируя все транзакции для данного client_id
                cur.execute("SELECT SUM(amount) FROM transactions WHERE client_id = ?", (client_id,))
                balance = cur.fetchone()[0] or 0  # Если нет транзакций, баланс равен 0

                # Формируем ответ с информацией о клиенте
                response = (f"Информация о клиенте:\n"
                            f"ID: {client_id}\n"
                            f"Имя: {name}\n"
                            f"Email: {email}\n"
                            f"Телефон: {phone}\n"
                            f"Баланс: {balance} руб.\n")
            else:
                response = f"Клиент с ID {client_id} не найден."

            # Отправляем информацию администратору
            bot.send_message(message.chat.id, response)

    except ValueError:
        bot.reply_to(message, "Неверный формат ID. Введите числовой ID клиента.")

@bot.message_handler(func=lambda message: message.text == "Просмотреть всех клиентов")
def view_all_clients(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        # Fetch all clients with basic information
        cur.execute("SELECT ID, name, email, phone FROM clients")
        clients = cur.fetchall()

        response = "Информация о клиентах:\n"
        for client in clients:
            client_id, name, email, phone = client

            # Calculate balance by summing up transactions for each client
            cur.execute("SELECT SUM(amount) FROM transactions WHERE client_id = ?", (client_id,))
            balance = cur.fetchone()[0] or 0  # If no transactions, balance is 0

            # Add client information to the response
            response += (f"ID: {client_id}\n"
                         f"Имя: {name}\n"
                         f"Email: {email}\n"
                         f"Телефон: {phone}\n"
                         f"Баланс: {balance} руб.\n\n")

        # Send the response to the admin
        bot.send_message(message.chat.id, response if clients else "Клиентов не найдено.")

def approve_application_by_id(message, application_type):
    try:
        application_id = int(message.text)
        approve_application(application_id, application_type, message)
    except ValueError:
        bot.reply_to(message, "Неверный формат ID. Введите число.")

# Функция для изменения статуса заявки на "Одобрен"
def approve_application(application_id, application_type, message):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        # Проверка на существование заявки с указанным ID и типом
        cur.execute("SELECT client_id, status, application_type FROM applications WHERE client_id = ? AND application_type = ?",
                    (application_id, application_type))
        application = cur.fetchone()

        if application:
            client_id, status, app_type = application
            # Проверка текущего статуса
            if status == "Ожидает":
                cur.execute("UPDATE applications SET status = 'Одобрен' WHERE client_id = ? AND application_type = ?",
                            (application_id, application_type))
                con.commit()
                bot.send_message(client_id, f"Ваша заявка на {application_type} была одобрена!")
                bot.reply_to(message, f"Заявка с ID {application_id} на {application_type} успешно одобрена.")
            else:
                bot.reply_to(message, f"Заявка с ID {application_id} уже одобрена или имеет другой статус.")
        else:
            bot.reply_to(message, f"Заявка с ID {application_id} на {application_type} не найдена.")
    except sqlite3.Error as e:
        bot.reply_to(message, f"Ошибка базы данных: {e}")
    finally:
        con.close()


# Обработчик команды для одобрения кредита
@bot.message_handler(func=lambda message: message.text == "Одобрить кредит по ID")
def approve_credit_request(message):
    bot.send_message(message.chat.id, "Введите ID заявки для одобрения кредита:")
    bot.register_next_step_handler(message, lambda msg: approve_application_by_id(msg, "Кредит"))


# Обработчик команды для одобрения страховки
@bot.message_handler(func=lambda message: message.text == "Одобрить страховку по ID")
def approve_insurance_request(message):
    bot.send_message(message.chat.id, "Введите ID заявки для одобрения страховки:")
    bot.register_next_step_handler(message, lambda msg: approve_application_by_id(msg, "Страхование"))


# Функция для регистрации пользователя
@bot.message_handler(commands=["start"])
def start(message):
    client_id = message.from_user.id
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients WHERE ID = ?", (client_id,))
        existing_user = cur.fetchone()

    if existing_user:
        bot.reply_to(message, "Вы уже зарегистрированы.")
        send_main_menu(message, client_id == ADMIN_ID)
    else:
        bot.send_message(message.chat.id, "Укажите ваше имя, телефон, email и пароль через пробел.")
        bot.register_next_step_handler(message, save_new_client)


# Функция для сохранения нового клиента
def save_new_client(message):
    user_data = message.text.strip().split()
    if len(user_data) < 4:
        bot.reply_to(message, "Укажите имя, номер телефона, email и пароль через пробел.")
        return

    full_name, phone_number, email, password = user_data[:4]
    client_id = message.from_user.id

    # Валидация данных
    if not (phone_number.isdigit() and len(phone_number) >= 10):
        bot.reply_to(message, "Укажите корректный номер телефона (минимум 10 цифр).")
        return
    if "@" not in email or "." not in email:
        bot.reply_to(message, "Укажите корректный email.")
        return
    if len(password) < 6:
        bot.reply_to(message, "Пароль должен содержать минимум 6 символов.")
        return

    # Сохранение данных в базу
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO clients (ID, name, email, password, phone) VALUES (?, ?, ?, ?, ?)",
                        (client_id, full_name, email, password, phone_number))
            con.commit()
        bot.reply_to(message, "Регистрация успешна!")
        send_main_menu(message, client_id == ADMIN_ID)
    except sqlite3.IntegrityError as e:
        bot.reply_to(message, f"Ошибка: {e}")
    except Exception as e:
        bot.reply_to(message, f"Неизвестная ошибка: {e}")


@bot.message_handler(func=lambda message: message.text == "Главное меню")
def go_to_main_menu(message):
    send_main_menu(message)


# Функция для запроса услуги
@bot.message_handler(func=lambda message: message.text == "Запросить услугу")
def request_service_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Взять кредит"),
               types.KeyboardButton("Страхование"),
               types.KeyboardButton("Посмотреть мои заявки"),
               types.KeyboardButton("Главное меню"))
    bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=markup)


# Функция для создания заявки на кредит
@bot.message_handler(func=lambda message: message.text == "Взять кредит")
def request_credit(message):
    add_application(message, "Кредит")


# Функция для создания заявки на страхование
@bot.message_handler(func=lambda message: message.text == "Страхование")
def request_insurance(message):
    add_application(message, "Страхование")


# Функция для добавления заявки
def add_application(message, application_type):
    client_id = message.from_user.id
    submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO applications (client_id, application_type, status, submission_date, comments) VALUES (?, ?, ?, ?, ?)",
            (client_id, application_type, "Ожидает", submission_date, ""))
        con.commit()

    bot.reply_to(message, f"Ваша заявка на {application_type} успешно отправлена!")
    send_main_menu(message)


# Функция для просмотра заявок клиента
@bot.message_handler(func=lambda message: message.text == "Посмотреть мои заявки")
def view_my_applications(message):
    client_id = message.from_user.id

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT application_type, status, submission_date FROM applications WHERE client_id = ?",
                    (client_id,))
        applications = cur.fetchall()

    response = "Ваши заявки:\n" + "\n".join([f"{app[0]} - Статус: {app[1]}, Дата: {app[2]}" for app in
                                             applications]) if applications else "У вас нет активных заявок."
    bot.send_message(message.chat.id, response)
    send_main_menu(message)


# Функция для админа: просмотр всех заявок
@bot.message_handler(func=lambda message: message.text == "Просмотреть все заявки")
def view_all_applications(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT client_id, application_type, status, submission_date FROM applications")
        applications = cur.fetchall()

    response = "Все заявки:\n" + "\n".join([f"Клиент {app[0]} - {app[1]}, Статус: {app[2]}, Дата: {app[3]}" for app in
                                            applications]) if applications else "На данный момент заявок нет."
    bot.send_message(message.chat.id, response)


# Функция для внесения денег на счёт
@bot.message_handler(func=lambda message: message.text == "Внести деньги на счёт")
def add_funds_start(message):
    bot.send_message(message.chat.id, "Введите сумму, которую хотите внести:")
    bot.register_next_step_handler(message, add_funds)


def add_funds(message):
    client_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.reply_to(message, "Введите положительную сумму.")
            return
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO transactions (client_id, transaction_type, amount, date) VALUES (?, ?, ?, ?)",
                        (client_id, "Пополнение", amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            con.commit()
        bot.reply_to(message, f"Ваш счёт пополнен на {amount} руб.")
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите корректную сумму.")
    send_main_menu(message)


# Функция для просмотра услуг клиента за последние 24 часа
@bot.message_handler(func=lambda message: message.text == "Просмотреть мои услуги")
def view_my_services(message):
    client_id = message.from_user.id
    last_24_hours = datetime.now() - timedelta(days=1)
    last_24_hours_str = last_24_hours.strftime('%Y-%m-%d %H:%M:%S')

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            "SELECT application_type, status, submission_date FROM applications WHERE client_id = ? AND submission_date >= ?",
            (client_id, last_24_hours_str))
        services = cur.fetchall()

    response = "Ваши услуги за последние 24 часа:\n" + "\n".join(
        [f"{service[0]} - Статус: {service[1]}, Дата: {service[2]}" for service in
         services]) if services else "У вас нет заявок за последние 24 часа."
    bot.send_message(message.chat.id, response)
    send_main_menu(message)


# Запуск бота
bot.polling(none_stop=True)
