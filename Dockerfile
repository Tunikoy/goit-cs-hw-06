# Базовий образ з Python
FROM python:3.10-slim

# Створюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файли з проєкту у контейнер
COPY . /app

# Встановлюємо залежності
RUN pip install --no-cache-dir pymongo

# Відкриваємо порти для HTTP і Socket серверів
EXPOSE 3000 5000

# Запускаємо основний файл
CMD ["python", "main.py"]