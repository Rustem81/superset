@echo off
set BACKUP_FILE=%1

if "%BACKUP_FILE%"=="" (
    echo Usage: restore_superset.bat ^<path_to_backup.db^>
    pause
    exit /b 1
)

if not exist "%BACKUP_FILE%" (
    echo ❌ Файл не найден: %BACKUP_FILE%
    pause
    exit /b 1
)

echo 🔄 Восстанавливаем Superset из %BACKUP_FILE%...

:: Останавливаем контейнеры
docker-compose down --remove-orphans

:: Поднимаем контейнер (чтобы был доступ к exec)
docker-compose up -d superset-app
timeout /t 15 >nul

:: Копируем бэкап в контейнер
docker cp "%BACKUP_FILE%" superset-app:/app/superset_home/superset.db

:: 🔥 Критически важно: Устанавливаем права ВНУТРИ контейнера
echo 🔧 Устанавливаем права на superset.db...
docker exec superset-app chown superset:superset /app/superset_home/superset.db
docker exec superset-app chmod 600 /app/superset_home/superset.db

:: Перезапускаем, чтобы права точно применились
docker-compose restart superset-app
timeout /t 10 >nul

echo ✅ Бэкап восстановлен и права установлены!
echo 🚀 Superset запущен
echo 🌐 Открой: http://localhost:8088

pause