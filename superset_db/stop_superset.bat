@echo off
echo 🛑 Останавливаем Superset для бэкапа...

:: Останавливаем контейнеры
docker-compose down

:: Создаём папку backups
if not exist backups mkdir backups

:: Копируем superset.db
docker cp superset-app:/app/superset_home/superset.db backups\superset_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db

echo ✅ Бэкап сохранён в папке backups\
pause