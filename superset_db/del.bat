@echo off
echo [INFO] Останавливаем Superset...
docker-compose down

echo [INFO] Удаляем метабазу SQLite...
if exist "superset.db" (
    del /f "superset.db"
    echo [SUCCESS] База данных удалена
) else (
    echo [INFO] Файл базы данных не найден
)

echo [INFO] Запускаем Superset заново...
docker-compose up -d

echo [SUCCESS] Superset полностью очищен и перезапущен!
echo При первом запуске нужно будет:
echo 1. Создать администратора: superset-init
echo 2. Настроить заново базы данных и дашборды
pause