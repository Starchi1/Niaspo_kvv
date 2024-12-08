FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем bot.py в контейнер
COPY app/bot.py /app/bot.py

# Копируем requirements.txt из корня проекта в контейнер
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Запускаем бота
CMD ["python", "/app/bot.py"]
