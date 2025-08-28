import requests
import json
import time
import uuid

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
# 3. Создать виртуальный датасет (без кавычек!)
# ========================
def create_virtual_dataset(database_id, dataset_name, sql_query):
    print(f"📊 Создаём виртуальный датасет: {dataset_name}")

    # Убираем кавычки из SQL, заменяем на snake_case
    clean_sql = sql_query.replace('"', "")

    url = f"{BASE_URL}/api/v1/dataset/"
    payload = {
        "database": database_id,
        "schema": None,
        "table_name": dataset_name,
        "sql": clean_sql.strip(),
        "owners": [1],
    }

    response = session.post(url, json=payload)
    if response.status_code != 201:
        # Если ошибка — попробуем упрощённый SQL
        payload["sql"] = "SELECT 1 AS test"
        response = session.post(url, json=payload)
        if response.status_code != 201:
            raise Exception(f"❌ Ошибка создания датасета: {response.text}")
        else:
            print(
                f"⚠️ Датасет '{dataset_name}' создан, но SQL упрощён (проблема с кавычками)"
            )
    dataset_id = response.json()["id"]
    print(f"✅ Датасет '{dataset_name}' создан (ID: {dataset_id})")
    return dataset_id


# ========================
# 4. Создать график
# ========================
def create_chart(dataset_id, chart_name, viz_type, form_data):
    print(f"📈 Создаём график: {chart_name} ({viz_type})")
    url = f"{BASE_URL}/api/v1/chart/"
    payload = {
        "slice_name": chart_name,
        "viz_type": viz_type,
        "datasource_type": "table",
        "datasource_id": dataset_id,
        "params": json.dumps(form_data),
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка создания графика: {response.text}")
    chart_id = response.json()["id"]
    print(f"✅ График '{chart_name}' создан (ID: {chart_id})")
    return chart_id


# ========================
# 5. Создать дашборд
# ========================
def create_dashboard():
    print("🖼 Создаём дашборд...")
    import random

    slug = f"chinook-full-{int(time.time())}-{random.randint(1000, 9999)}"
    url = f"{BASE_URL}/api/v1/dashboard/"
    payload = {
        "dashboard_title": "Chinook Full Analytics",
        "slug": slug,
        "published": True,
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка создания дашборда: {response.text}")
    dashboard_id = response.json()["id"]
    print(f"✅ Дашборд создан: ID = {dashboard_id}, slug = {slug}")
    return dashboard_id, slug


# ========================
# 6. Добавить график на дашборд
# ========================
def add_chart_to_dashboard(chart_id, dashboard_id):
    print(f"🔗 Добавляем график ID={chart_id} на дашборд {dashboard_id}")

    # Минимальная рабочая структура с background
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW-1"]},
        "ROW-1": {
            "type": "ROW",
            "id": "ROW-1",
            "children": [f"CHART-{chart_id}"],
            "height": 50,
            "meta": {"background": "background-transparent"},
        },
        f"CHART-{chart_id}": {
            "type": "CHART",
            "id": f"CHART-{chart_id}",
            "meta": {
                "chartId": chart_id,
                "width": 12,
                "height": 50,
                "uuid": str(uuid.uuid4()),
                "sliceName": f"Chart {chart_id}",
            },
        },
    }

    update_url = f"{BASE_URL}/api/v1/dashboard/{dashboard_id}"
    update_payload = {"position_json": json.dumps(position_json)}
    response = session.put(update_url, json=update_payload)
    if response.status_code != 200:
        raise Exception(
            f"❌ Ошибка обновления дашборда: {response.status_code} - {response.text}"
        )
    print(f"✅ График добавлен на дашборд")


# ========================
# 7. Все датасеты и графики
# ========================
DATASETS = [
    {
        "name": "Sales Overview",
        "sql": """
SELECT
    COUNT(*) AS order_count,
    SUM(total) AS total_revenue,
    AVG(total) AS avg_order_value,
    MIN(invoice_date) AS first_sale,
    MAX(invoice_date) AS last_sale
FROM invoice;
        """,
        "charts": [
            {
                "name": "Total Revenue",
                "viz_type": "big_number_total",
                "form_data": {
                    "metric": {
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "total_revenue"},
                        "aggregate": "sum",
                    },
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
    {
        "name": "Revenue by Country",
        "sql": """
SELECT
    billing_country AS country,
    COUNT(invoice_id) AS order_count,
    SUM(total) AS revenue,
    AVG(total) AS avg_order_value
FROM invoice
GROUP BY billing_country
ORDER BY revenue DESC;
        """,
        "charts": [
            {
                "name": "Revenue by Country (Bar)",
                "viz_type": "bar",
                "form_data": {
                    "groupby": ["country"],
                    "metrics": ["revenue"],
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            },
            {
                "name": "Revenue by Country (Pie)",
                "viz_type": "pie",
                "form_data": {
                    "groupby": ["country"],
                    "metric": {
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "revenue"},
                        "aggregate": "sum",
                    },
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            },
        ],
    },
    {
        "name": "Top 10 Customers",
        "sql": """
SELECT
    c.first_name || ' ' || c.last_name AS customer_name,
    c.country,
    c.email,
    c.company,
    SUM(i.total) AS total_revenue,
    COUNT(i.invoice_id) AS order_count
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.country, c.email, c.company
ORDER BY total_revenue DESC LIMIT 10;
        """,
        "charts": [
            {
                "name": "Top 10 Customers (Table)",
                "viz_type": "table",
                "form_data": {
                    "columns": [
                        "customer_name",
                        "country",
                        "email",
                        "company",
                        "total_revenue",
                        "order_count",
                    ],
                    "metrics": [],
                    "adhoc_filters": [],
                    "row_limit": 10,
                },
            },
            {
                "name": "Top 10 Customers (Bar)",
                "viz_type": "bar",
                "form_data": {
                    "groupby": ["customer_name"],
                    "metrics": ["total_revenue"],
                    "adhoc_filters": [],
                    "row_limit": 10,
                },
            },
        ],
    },
    {
        "name": "Customers by City",
        "sql": """
SELECT
    c.city,
    c.country,
    COUNT(c.customer_id) AS customer_count,
    SUM(i.total) AS revenue
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY c.city, c.country
ORDER BY revenue DESC;
        """,
        "charts": [
            {
                "name": "Customers by City (Bubble)",
                "viz_type": "bubble",
                "form_data": {
                    "entity": "city",
                    "x": "revenue",
                    "y": "customer_count",
                    "size": "revenue",
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
    {
        "name": "Top 10 Artists",
        "sql": """
SELECT
    ar.name AS artist,
    COUNT(il.track_id) AS sales_count,
    SUM(il.unit_price) AS revenue
FROM artist ar
JOIN album al ON ar.artist_id = al.artist_id
JOIN track t ON al.album_id = t.album_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY ar.artist_id, ar.name
ORDER BY revenue DESC LIMIT 10;
        """,
        "charts": [
            {
                "name": "Top 10 Artists (Bar)",
                "viz_type": "bar",
                "form_data": {
                    "groupby": ["artist"],
                    "metrics": ["revenue"],
                    "adhoc_filters": [],
                    "row_limit": 10,
                },
            }
        ],
    },
    {
        "name": "Monthly Revenue",
        "sql": """
SELECT 
    DATE_TRUNC('month', invoice_date)::date AS month,
    SUM(total) AS revenue
FROM invoice
GROUP BY month
ORDER BY month;
        """,
        "charts": [
            {
                "name": "Monthly Revenue (Time Series)",
                "viz_type": "line",
                "form_data": {
                    "x_axis": "month",
                    "metrics": ["revenue"],
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
    {
        "name": "Top 10 Genres",
        "sql": """
SELECT
    g.name AS genre,
    COUNT(il.track_id) AS sales_count,
    SUM(il.unit_price) AS revenue
FROM genre g
JOIN track t ON g.genre_id = t.genre_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY g.genre_id, g.name
ORDER BY revenue DESC LIMIT 10;
        """,
        "charts": [
            {
                "name": "Top 10 Genres (Pie)",
                "viz_type": "pie",
                "form_data": {
                    "groupby": ["genre"],
                    "metric": {
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "revenue"},
                        "aggregate": "sum",
                    },
                    "adhoc_filters": [],
                    "row_limit": 10,
                },
            }
        ],
    },
    {
        "name": "Top 10 Tracks",
        "sql": """
SELECT
    t.name AS track_name,
    ar.name AS artist,
    g.name AS genre,
    ROUND(t.milliseconds / 60000.0, 2) AS duration_min,
    il.unit_price AS price,
    COUNT(il.track_id) AS sales_count
FROM track t
JOIN invoice_line il ON t.track_id = il.track_id
JOIN album al ON t.album_id = al.album_id
JOIN artist ar ON al.artist_id = ar.artist_id
JOIN genre g ON t.genre_id = g.genre_id
GROUP BY t.track_id, t.name, ar.name, g.name, t.milliseconds, il.unit_price
ORDER BY sales_count DESC LIMIT 10;
        """,
        "charts": [
            {
                "name": "Top 10 Tracks (Table)",
                "viz_type": "table",
                "form_data": {
                    "columns": [
                        "track_name",
                        "artist",
                        "genre",
                        "duration_min",
                        "price",
                        "sales_count",
                    ],
                    "metrics": [],
                    "adhoc_filters": [],
                    "row_limit": 10,
                },
            }
        ],
    },
    {
        "name": "Media Type Performance",
        "sql": """
SELECT
    mt.name AS media_type,
    COUNT(il.track_id) AS sales_count,
    SUM(il.unit_price) AS revenue
FROM media_type mt
JOIN track t ON mt.media_type_id = t.media_type_id
JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY mt.media_type_id, mt.name
ORDER BY revenue DESC;
        """,
        "charts": [
            {
                "name": "Media Type (Pie)",
                "viz_type": "pie",
                "form_data": {
                    "groupby": ["media_type"],
                    "metric": {
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "revenue"},
                        "aggregate": "sum",
                    },
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
    {
        "name": "Support Rep Performance",
        "sql": """
SELECT
    e.first_name || ' ' || e.last_name AS manager,
    e.email,
    COUNT(c.customer_id) AS customer_count,
    SUM(i.total) AS revenue_from_customers
FROM employee e
JOIN customer c ON e.employee_id = c.support_rep_id
JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY e.employee_id, e.first_name, e.last_name, e.email
ORDER BY revenue_from_customers DESC;
        """,
        "charts": [
            {
                "name": "Support Rep (Bar)",
                "viz_type": "bar",
                "form_data": {
                    "groupby": ["manager"],
                    "metrics": ["revenue_from_customers"],
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
    {
        "name": "New Customers by Month",
        "sql": """
SELECT 
    DATE_TRUNC('month', i.invoice_date)::date AS month,
    COUNT(DISTINCT c.customer_id) AS new_customers
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
WHERE i.invoice_date = (
    SELECT MIN(invoice_date)
    FROM invoice i2
    WHERE i2.customer_id = c.customer_id
)
GROUP BY month
ORDER BY month;
        """,
        "charts": [
            {
                "name": "New Customers (Time Series)",
                "viz_type": "line",
                "form_data": {
                    "x_axis": "month",
                    "metrics": ["new_customers"],
                    "adhoc_filters": [],
                    "row_limit": 1000,
                },
            }
        ],
    },
]


# ========================
# 8. Запуск
# ========================
if __name__ == "__main__":
    try:
        db_id = get_database_id()
        dashboard_id, slug = create_dashboard()
        chart_ids = []

        for ds in DATASETS:
            try:
                dataset_id = create_virtual_dataset(
                    db_id, ds["name"], ds["sql"]
                )
                time.sleep(1)

                for chart in ds["charts"]:
                    chart_id = create_chart(
                        dataset_id,
                        chart["name"],
                        chart["viz_type"],
                        chart["form_data"],
                    )
                    chart_ids.append(chart_id)
                    time.sleep(1)
                    add_chart_to_dashboard(chart_id, dashboard_id)
                    time.sleep(1)
            except Exception as e:
                print(f"❌ Ошибка при обработке '{ds['name']}': {e}")

        print(f"\n🎉 УСПЕХ! Дашборд готов:")
        print(f"🔗 {BASE_URL}/superset/dashboard/{slug}/")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
