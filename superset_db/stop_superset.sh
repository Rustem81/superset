#!/bin/bash
# stop_superset.sh

echo "🛑 Останавливаем Superset для бэкапа..."

# Останавливаем контейнер
docker-compose down

# Копируем superset.db в папку backups
mkdir -p ./backups
docker cp superset-app:/app/superset_home/superset.db ./backups/superset_$(date +%Y%m%d_%H%M%S).db

echo "✅ Бэкап метабазы Superset сохранён в ./backups/"
echo "💡 Теперь можно закрыть терминал или продолжить"