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
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )
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
# 3. Создать виртуальный датасет
# ========================
def create_virtual_dataset(database_id, dataset_name, sql_query):
    print(f"📊 Создаём виртуальный датасет: {dataset_name}")

    url = f"{BASE_URL}/api/v1/dataset/"
    payload = {
        "database": database_id,
        "schema": None,
        "table_name": dataset_name,
        "sql": sql_query.strip(),
        "owners": [1],
    }

    response = session.post(url, json=payload)
    if response.status_code != 201:
        error_msg = response.text
        print(f"⚠️ Ошибка создания датасета '{dataset_name}': {error_msg}")
        return None

    dataset_id = response.json()["id"]
    print(f"✅ Датасет '{dataset_name}' создан (ID: {dataset_id})")
    return dataset_id


# ========================
# 4. Получить все доступные viz_types
# ========================
def get_available_viz_types():
    """Получить список доступных типов визуализаций"""
    print("🔍 Получаем доступные типы визуализаций...")
    url = f"{BASE_URL}/api/v1/chart/_info"
    response = session.get(url)
    if response.status_code == 200:
        data = response.json()
        # Ищем список визуализаций
        if (
            "form_data_schema" in data
            and "definitions" in data["form_data_schema"]
        ):
            definitions = data["form_data_schema"]["definitions"]
            # viz_types находится в VizType
            if "VizType" in definitions:
                viz_types = definitions["VizType"]["enum"]
                print("✅ Доступные типы визуализаций:")
                for viz_type in viz_types:
                    print(f"   - {viz_type}")
                return viz_types
            else:
                print("⚠️ 'VizType' не найден в definitions")
        else:
            print(
                "⚠️ 'form_data_schema' или 'definitions' отсутствуют в ответе"
            )
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
    return []


# ========================
# 5. Создать график
# ========================
def create_chart(dataset_id, chart_name, viz_type, form_data):
    print(f"📈 Создаём график: {chart_name} ({viz_type})")

    # Добавляем обязательные поля
    form_data["datasource"] = f"{dataset_id}__table"
    form_data["viz_type"] = viz_type
    form_data["row_limit"] = 1000

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
        error_msg = response.text
        print(f"❌ Ошибка создания графика '{chart_name}': {error_msg}")
        return None

    chart_id = response.json()["id"]
    print(f"✅ График '{chart_name}' создан (ID: {chart_id})")
    return chart_id


# ========================
# 6. Создать дашборд
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
# 7. Добавить график на дашборд
# ========================
def add_chart_to_dashboard(chart_id, dashboard_id):
    print(f"🔗 Добавляем график ID={chart_id} на дашборд {dashboard_id}")

    # Сначала получаем текущую конфигурацию дашборда
    url = f"{BASE_URL}/api/v1/dashboard/{dashboard_id}"
    response = session.get(url)

    if response.status_code != 200:
        print(f"⚠️ Не удалось получить дашборд: {response.text}")
        return False

    try:
        dashboard_data = response.json()
        result_data = dashboard_data.get("result", {})

        position_json = result_data.get("position_json", {})

        if isinstance(position_json, str):
            try:
                position_json = json.loads(position_json)
            except json.JSONDecodeError:
                position_json = {}

        if not position_json:
            position_json = {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {
                    "type": "ROOT",
                    "id": "ROOT_ID",
                    "children": ["GRID_ID"],
                },
                "GRID_ID": {
                    "type": "GRID",
                    "id": "GRID_ID",
                    "children": ["ROW-1"],
                },
                "ROW-1": {"type": "ROW", "id": "ROW-1", "children": []},
            }

        chart_key = f"CHART-{chart_id}-{uuid.uuid4().hex[:8]}"

        position_json[chart_key] = {
            "type": "CHART",
            "id": chart_key,
            "meta": {
                "chartId": chart_id,
                "width": 6,
                "height": 50,
                "uuid": str(uuid.uuid4()),
            },
        }

        if "ROW-1" in position_json:
            if "children" not in position_json["ROW-1"]:
                position_json["ROW-1"]["children"] = []
            position_json["ROW-1"]["children"].append(chart_key)

        update_payload = {"position_json": json.dumps(position_json)}
        response = session.put(url, json=update_payload)

        if response.status_code == 200:
            print(f"✅ График {chart_id} успешно добавлен на дашборд")
            return True
        else:
            print(f"❌ Ошибка обновления дашборда: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при добавлении графика: {e}")
        return False


# ========================
# 8. ИСПРАВЛЕННЫЕ ДАТАСЕТЫ И ГРАФИКИ (ПРАВИЛЬНЫЕ VIZ_TYPES)
# ========================
DATASETS = [
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
                "name": "Customers by City (Table)",
                "viz_type": "table",
                "form_data": {
                    "all_columns": [
                        "city",
                        "country",
                        "customer_count",
                        "revenue",
                    ],
                    "page_length": 20,
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
ORDER BY sales_count DESC
LIMIT 10;
""",
        "charts": [
            {
                "name": "Top 10 Tracks (Table)",
                "viz_type": "table",
                "form_data": {
                    "all_columns": [
                        "track_name",
                        "artist",
                        "genre",
                        "duration_min",
                        "price",
                        "sales_count",
                    ],
                    "page_length": 10,
                },
            }
        ],
    },
]

# ========================
# 9. Запуск
# ========================
if __name__ == "__main__":
    try:
        print("🚀 Запуск создания дашборда...")

        # Получаем доступные типы визуализаций
        available_viz_types = get_available_viz_types()

        db_id = get_database_id()
        print(f"✅ Используем database_id: {db_id}")

        dashboard_id, slug = create_dashboard()
        chart_ids = []
        successful_charts = 0

        for i, ds in enumerate(DATASETS):
            try:
                print(f"\n{'=' * 50}")
                print(
                    f"Обрабатываем датасет {i + 1}/{len(DATASETS)}: {ds['name']}"
                )

                # Проверяем, поддерживается ли viz_type
                for chart in ds["charts"]:
                    if chart["viz_type"] not in available_viz_types:
                        print(
                            f"⚠️  viz_type '{chart['viz_type']}' не поддерживается! Доступные: {available_viz_types}"
                        )
                        # Пробуем альтернативные варианты
                        if chart["viz_type"] == "pie":
                            chart["viz_type"] = "pie_chart"
                        elif chart["viz_type"] == "line":
                            chart["viz_type"] = "time_series"
                        elif chart["viz_type"] == "bar":
                            chart["viz_type"] = "dist_bar"

                dataset_id = create_virtual_dataset(
                    db_id, ds["name"], ds["sql"]
                )
                if not dataset_id:
                    continue

                time.sleep(2)

                for j, chart in enumerate(ds["charts"]):
                    try:
                        print(
                            f"  Создаем график {j + 1}: {chart['name']} ({chart['viz_type']})"
                        )

                        chart_id = create_chart(
                            dataset_id,
                            chart["name"],
                            chart["viz_type"],
                            chart["form_data"],
                        )
                        if chart_id:
                            chart_ids.append(chart_id)
                            time.sleep(2)

                            if add_chart_to_dashboard(chart_id, dashboard_id):
                                successful_charts += 1
                            time.sleep(1)

                    except Exception as e:
                        print(f"❌ Ошибка при создании графика: {e}")
                        continue

            except Exception as e:
                print(f"❌ Ошибка при обработке датасета '{ds['name']}': {e}")
                continue

        print(f"\n{'=' * 50}")
        print("🎯 РЕЗУЛЬТАТ:")
        print(
            f"✅ Успешно создано графиков: {successful_charts}/{len(chart_ids)}"
        )
        print(f"🔗 Дашборд: {BASE_URL}/superset/dashboard/{slug}/")

        if successful_charts > 0:
            print("🎉 Дашборд успешно создан!")
            print("📊 Проверьте дашборд в веб-интерфейсе Superset")
        else:
            print("\n⚠️  Не удалось создать ни одного графика!")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
