# Спецификация

# Спецификация

## Docker

PG запускается с базой данных Chinook [Chinook Database](https://github.com/lerocha/chinook-database).

![Схема базы данных Chinook](./chinook_serial.png)

```bash
docker-compose up -d # запуск контейнеров SuperSet + PG
```

## auto_super

```bash
pyshon ./delete_superset.py # удалить все метаданные в сеперсете
```

```bash
pyshon ./datasets_create.py # создать датасеты
```

## superset_restore

### import_superset_artifacts.py

✅ Авторизуется в Superset
✅ Импортирует подключение к БД
✅ Импортирует датасеты
✅ Импортирует графики
✅ Импортирует дашборд

### export_superset_artifacts.py

✅ Авторизуется в Superset
✅ Экспортирует подключение к БД
✅ Экспортирует все датасеты
✅ Экспортирует все графики
✅ Экспортирует весь дашборд
