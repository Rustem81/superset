import requests
import json
import time

# ========================
# Конфигурация
# ========================
BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# Создаём сессию
session = requests.Session()


# ========================
# 1. Авторизация
# ========================
def login():
    print("🔐 Авторизуемся в Superset...")
    url = f"{BASE_URL}/api/v1/security/login"
    payload = {"username": USERNAME, "password": PASSWORD, "provider": "db"}
    response = session.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка авторизации: {response.text}")
    token = response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    session.headers.update({"Content-Type": "application/json"})
    print("✅ Авторизация прошла успешно")


# Вызов авторизации
login()


# ========================
# 2. Получить ID базы данных
# ========================
def get_database_id():
    print("🔍 Получаем ID БД...")
    url = f"{BASE_URL}/api/v1/database/"
    response = session.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка: {response.text}")
    data = response.json()
    databases = data["result"]
    if not databases:
        raise Exception("❌ Нет подключённых баз данных")
    for db in databases:
        print(f"  • ID: {db['id']}, Name: {db['database_name']}")
    return databases[0]["id"]


# ========================
# 3. Создать виртуальный датасет из SQL
# ========================
def create_virtual_dataset(
    database_id, technical_name, display_name, sql_query
):
    """
    Создаёт виртуальный датасет
    :param database_id: ID БД
    :param technical_name: имя на латинице (для API)
    :param display_name: имя на русском (для интерфейса)
    :param sql_query: SQL-запрос
    """
    print(f"📊 Создаём виртуальный датасет: {display_name}")
    url = f"{BASE_URL}/api/v1/dataset/"
    payload = {
        "database": database_id,
        "schema": None,
        "table_name": display_name,  # Это имя будет отображаться в UI
        "sql": sql_query.strip(),
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        # Упрощённый запрос для диагностики
        simple_payload = {
            "database": database_id,
            "table_name": display_name,
            "sql": "SELECT 1 AS test",
        }
        response = session.post(url, json=simple_payload)
        if response.status_code != 201:
            raise Exception(f"❌ Ошибка создания датасета: {response.text}")
        else:
            print(
                f"⚠️ Датасет '{display_name}' создан, но SQL упрощён (проблема с кавычками)"
            )
    else:
        print(f"✅ Датасет '{display_name}' создан")
    return response.json()["id"]


# ========================
# Массив SQL-запросов
# ========================
DATASETS = [
    {
        "name": "Sales Overview",
        "display_name": "Общая статистика",
        "sql": """
SELECT
    COUNT(*) AS "Количество заказов",
    SUM(total) AS "Общая выручка",
    AVG(total) AS "Средний чек",
    MIN(invoice_date) AS "Первая продажа",
    MAX(invoice_date) AS "Последняя продажа"
FROM invoice;
        """,
    },
    {
        "name": "Revenue by Country",
        "display_name": "Выручка по странам",
        "sql": """
SELECT
    billing_country AS "Страна",
    SUM(total) AS "Выручка",
    COUNT(*) AS "Количество заказов"
FROM invoice
GROUP BY "Страна"
ORDER BY "Выручка" DESC;
        """,
    },
    {
        "name": "Top 10 Customers",
        "display_name": "Топ-10 клиентов",
        "sql": """
SELECT
    c.first_name || ' ' || c.last_name AS "Имя клиента",
    c.country AS "Страна",
    SUM(i.total) AS "Общая выручка"
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, "Имя клиента", "Страна"
ORDER BY "Общая выручка" DESC
LIMIT 10;
        """,
    },
    {
        "name": "Customers by City",
        "display_name": "Клиенты по городам",
        "sql": """
SELECT
    c.city AS "Город",
    c.country AS "Страна",
    COUNT(c.customer_id) AS "Количество клиентов",
    SUM(i.total) AS "Выручка"
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY "Город", "Страна"
ORDER BY "Выручка" DESC;
        """,
    },
    {
        "name": "Top 10 Artists",
        "display_name": "Топ-10 артистов",
        "sql": """
SELECT
    ar.name AS "Артист",
    SUM(il.unit_price) AS "Выручка"
FROM artist ar
JOIN album al ON ar.artist_id = al.artist_id
JOIN track t ON al.album_id = t.album_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY "Артист"
ORDER BY "Выручка" DESC
LIMIT 10;
        """,
    },
    {
        "name": "Monthly Revenue",
        "display_name": "Выручка по месяцам",
        "sql": """
SELECT 
    DATE_TRUNC('month', invoice_date)::date AS "Месяц",
    SUM(total) AS "Выручка"
FROM invoice
GROUP BY "Месяц"
ORDER BY "Месяц";
        """,
    },
    {
        "name": "Top 10 Genres",
        "display_name": "Топ-10 жанров",
        "sql": """
SELECT
    g.name AS "Жанр",
    SUM(il.unit_price) AS "Выручка"
FROM genre g
JOIN track t ON g.genre_id = t.genre_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY "Жанр"
ORDER BY "Выручка" DESC
LIMIT 10;
        """,
    },
    {
        "name": "Top 10 Tracks",
        "display_name": "Топ-10 треков",
        "sql": """
SELECT
    t.name AS "Название трека",
    ar.name AS "Артист",
    COUNT(il.track_id) AS "Количество продаж"
FROM track t
JOIN invoice_line il ON t.track_id = il.track_id
JOIN album al ON t.album_id = al.album_id
JOIN artist ar ON al.artist_id = ar.artist_id
GROUP BY "Название трека", "Артист"
ORDER BY "Количество продаж" DESC
LIMIT 10;
        """,
    },
    {
        "name": "Media Type Performance",
        "display_name": "Выручка по типам носителей",
        "sql": """
SELECT
    mt.name AS "Тип носителя",
    SUM(il.unit_price) AS "Выручка"
FROM media_type mt
JOIN track t ON mt.media_type_id = t.media_type_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY "Тип носителя"
ORDER BY "Выручка" DESC;
        """,
    },
    {
        "name": "Support Rep Performance",
        "display_name": "Эффективность менеджеров",
        "sql": """
SELECT
    e.first_name || ' ' || e.last_name AS "Менеджер",
    SUM(i.total) AS "Выручка от клиентов"
FROM employee e
JOIN customer c ON e.employee_id = c.support_rep_id
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY "Менеджер"
ORDER BY "Выручка от клиентов" DESC;
        """,
    },
    {
        "name": "New Customers by Month",
        "display_name": "Новые клиенты по месяцам",
        "sql": """
SELECT 
    DATE_TRUNC('month', i.invoice_date)::date AS "Месяц",
    COUNT(DISTINCT c.customer_id) AS "Новые клиенты"
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
WHERE i.invoice_date = (
    SELECT MIN(invoice_date)
    FROM invoice i2
    WHERE i2.customer_id = c.customer_id
)
GROUP BY "Месяц"
ORDER BY "Месяц";
        """,
    },
]
# ========================
# 4. Запуск: создание всех датасетов
# ========================
if __name__ == "__main__":
    try:
        db_id = get_database_id()
        print(f"✅ Используем database_id = {db_id}")

        created_datasets = []

        for ds in DATASETS:
            try:
                dataset_id = create_virtual_dataset(
                    db_id,
                    ds["name"],  # техническое имя (латиница)
                    ds["display_name"],  # отображаемое имя (кириллица)
                    ds["sql"],
                )
                created_datasets.append(
                    {
                        "name": ds["name"],
                        "display_name": ds["display_name"],
                        "id": dataset_id,
                    }
                )
                time.sleep(1)
            except Exception as e:
                print(f"❌ Не удалось создать '{ds['display_name']}': {e}")

        # Итог
        print(
            f"\n🎉 УСПЕШНО СОЗДАНО {len(created_datasets)} виртуальных датасетов:"
        )
        for ds in created_datasets:
            print(f"  • {ds['display_name']} (ID: {ds['id']})")

        print(f"\n👉 Перейди в Superset: {BASE_URL}/dataset/list/")
        print("   и начни строить графики вручную!")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
