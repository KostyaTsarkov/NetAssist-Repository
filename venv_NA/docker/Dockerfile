# Используем базовый образ с Python 3.9
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt requirements.txt

# Обновляем pip
RUN python -m pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем код приложения
COPY . .

# Запускаем приложение
CMD ["python", "app.py"]
