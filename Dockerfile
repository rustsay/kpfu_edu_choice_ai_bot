# Образ для Telegram-бота экспертной системы КФУ
FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения и данные
COPY bot.py config.py .
COPY handlers/ handlers/
COPY services/ services/
COPY utils/ utils/
# Основные JSON-файлы с программами
COPY kfu_programs_by_institute.json kfu_programs.json full_decision_tree.json mag_baz.json .

# Переменные окружения передаются при запуске (env_file или --env)
# Точка входа
CMD ["python", "-u", "bot.py"]
