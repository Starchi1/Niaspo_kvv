# Dockerfile для Telebot
FROM python:3.9

# Установка необходимых библиотек
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY .. .

# Запуск бота
CMD ["python", "bot.py"]