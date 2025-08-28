#!/bin/bash
# restore_superset.sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <path_to_backup.db>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл не найден: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Восстанавливаем Superset из $BACKUP_FILE..."

# Удаляем старый контейнер
docker-compose down --remove-orphans

# Копируем бэкап в контейнер
docker-compose up -d --build
sleep 5

# Заменяем superset.db
docker cp "$BACKUP_FILE" superset-app:/app/superset_home/superset.db

echo "✅ Бэкап восстановлен!"
echo "🚀 Superset запущен"
echo "🌐 Открой: http://localhost:8088"