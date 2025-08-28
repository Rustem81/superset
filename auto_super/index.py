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


# Вызов авторизации
login()


# ========================
# 2. Получить ID базы данных
# ========================
def get_database_id():
    print("🔍 Получаем список баз данных...")
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
    return databases[0]["id"]  # Возвращаем первый


# ========================
# 3. Создать датасет
# ========================
def create_dataset(database_id):
    print("📊 Создаём датасет из таблицы customer...")
    url = f"{BASE_URL}/api/v1/dataset/"
    payload = {
        "database": database_id,
        "schema": "public",
        "table_name": "customer",
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка создания датасета: {response.text}")
    dataset_id = response.json()["id"]
    print(f"✅ Датасет создан: ID = {dataset_id}")
    return dataset_id


# ========================
# 4. Создать график Big Number (общее количество)
# ========================
def create_big_number_chart(dataset_id):
    print("📈 Создаём график Big Number (Total Customers)...")
    url = f"{BASE_URL}/api/v1/chart/"
    form_data = {
        "datasource": f"{dataset_id}__table",
        "viz_type": "big_number_total",
        "metric": {
            "expressionType": "SIMPLE",
            "column": {"column_name": "count", "type": "BIGINT"},
            "aggregate": "sum",
            "label": "Total Customers",
        },
        "adhoc_filters": [],
        "row_limit": 1000,
    }
    payload = {
        "slice_name": "Total Customers",
        "viz_type": "big_number_total",
        "datasource_type": "table",
        "datasource_id": dataset_id,
        "params": json.dumps(form_data),
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка создания графика: {response.text}")
    chart_id = response.json()["id"]
    print(f"✅ График Big Number создан: ID = {chart_id}")
    return chart_id


# ========================
# 5. Создать таблицу (клиенты по странам)
# ========================
def create_table_chart(dataset_id):
    print("📊 Создаём таблицу 'Customers by Country'...")
    url = f"{BASE_URL}/api/v1/chart/"
    form_data = {
        "datasource": f"{dataset_id}__table",
        "viz_type": "table",
        "metrics": ["count"],
        "groupby": ["country"],
        "adhoc_filters": [],
        "row_limit": 1000,
        "table_timestamp_format": "smart_date",
        "include_time": False,
    }
    payload = {
        "slice_name": "Customers by Country",
        "viz_type": "table",
        "datasource_type": "table",
        "datasource_id": dataset_id,
        "params": json.dumps(form_data),
        "owners": [1],
    }
    response = session.post(url, json=payload)
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка создания таблицы: {response.text}")
    chart_id = response.json()["id"]
    print(f"✅ Таблица создана: ID = {chart_id}")
    return chart_id


# ========================
# 6. Создать дашборд
# ========================
def create_dashboard():
    print("🖼 Создаём дашборд...")
    import random

    slug = f"chinook-auto-{int(time.time())}-{random.randint(1000, 9999)}"
    url = f"{BASE_URL}/api/v1/dashboard/"
    payload = {
        "dashboard_title": "Chinook Auto Dashboard",
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
# 7. Добавить график на дашборд (исправленный position_json)
# ========================
def add_chart_to_dashboard(chart_id, dashboard_id):
    print("🔗 Добавляем график на дашборд...")
    # Минимальная рабочая структура
    position_json = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW-1"]},
        "ROW-1": {
            "type": "ROW",
            "id": "ROW-1",
            "children": [f"CHART-{chart_id}"],
            "height": 50,
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

    print(f"✅ График добавлен на дашборд {dashboard_id}")


# ========================
# 8. Запуск всего пайплайна
# ========================
if __name__ == "__main__":
    try:
        # 1. Получаем ID БД
        db_id = get_database_id()
        print(f"✅ Используем database_id = {db_id}")

        # 2. Создаём датасет
        dataset_id = create_dataset(db_id)
        time.sleep(2)

        # 3. Создаём графики
        big_number_chart_id = create_big_number_chart(dataset_id)
        time.sleep(2)
        table_chart_id = create_table_chart(dataset_id)
        time.sleep(2)

        # 4. Создаём дашборд
        dashboard_id, slug = create_dashboard()
        time.sleep(2)

        # 5. Добавляем графики
        add_chart_to_dashboard(big_number_chart_id, dashboard_id)
        # time.sleep(2)
        # add_chart_to_dashboard(table_chart_id, dashboard_id)

        # 6. Готово!
        print(f"\n🎉 УСПЕХ! Дашборд готов:")
        print(f"🔗 {BASE_URL}/superset/dashboard/{slug}/")
        print(f"📊 Прямая ссылка: {BASE_URL}/dashboard/{dashboard_id}/view")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
