# superset_config.py

# 🔥 Отключаем CSRF — критично для API
WTF_CSRF_ENABLED = False

# 🔥 Отключаем Talisman (HTTPS-редиректы), чтобы не мешал в dev
TALISMAN_ENABLED = False

# 🌐 Superset будет слушать 0.0.0.0 (все интерфейсы)
# Это уже делается через команду, но можно и здесь
# (не обязательно, если в command есть -h 0.0.0.0)

# 📁 Путь к метабазе (если используешь SQLite)
# Если оставить закомментированным — Superset возьмёт из DATABASE_URL
# SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# 🔐 Секретный ключ
SECRET_KEY = "A0Zr98j/3yX R~XHH!jmN]LWX/,?RT"

# 📊 Логирование
LOG_LEVEL = "INFO"
ENABLE_TIME_ROTATING = True

# 🖼 Скриншоты и PDF (если нужен функционал)
# Если не установлен pillow, будет предупреждение
# Но не ошибка

# 🚫 Отключаем проверку на production (только для разработки!)
FLASK_ENV = "development"


CUSTOM_SECURITY_MANAGER = None
ENABLE_JAVASCRIPT_CONTROLS = True
DASHBOARD_CSS = True  # Включает редактор CSS в дашборде


# 🧩 Дополнительные настройки
# Например, отключить анимации в интерфейсе
# или изменить поведение фильтров

print("✅ superset_config.py загружен!")
