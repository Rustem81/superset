@echo off
:: ========================
:: Бэкап метабазы Superset (SQLite)
:: ========================

echo Останавливаем контейнеры...
docker-compose down
if %errorlevel% neq 0 (
    echo Предупреждение: не удалось остановить контейнеры
)

if not exist backups mkdir backups

echo Бэкап superset.db...
docker cp superset-app:/app/superset_home/superset.db backups\superset_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%.db

if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось скопировать базу данных
    pause
    exit /b 1
)

echo Бэкап успешно завершен!
echo Файл: backups\superset_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%.db

dir backups\
pause