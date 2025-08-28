FROM apache/superset:latest

# Переключаемся на root
USER root

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Убедимся, что pip установлен в виртуальном окружении
# Проверим, существует ли /app/.venv/bin/pip
RUN if [ -f /app/.venv/bin/pip ]; then \
      echo "✅ pip уже существует в /app/.venv/bin/pip"; \
    else \
      echo "🔧 pip отсутствует — устанавливаем через ensurepip..."; \
      python -m ensurepip --upgrade || echo "⚠️ ensurepip не сработал, пробуем вручную"; \
    fi

# Даже если ensurepip не сработал — попробуем установить через python -m pip
# Или через /usr/local/bin/python -m pip
RUN python -m pip install psycopg2-binary --no-cache-dir --force-reinstall || \
    /usr/local/bin/python -m pip install psycopg2-binary --no-cache-dir --force-reinstall

# Проверяем, что модуль импортируется
RUN python -c "import psycopg2; print('🎉 psycopg2 успешно установлен и импортирован!')"

# Возвращаемся к пользователю superset
USER superset