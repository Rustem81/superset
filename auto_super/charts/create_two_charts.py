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


# ========================
# 2. Получить ID датасета по имени
# ========================
def get_dataset_id_by_name(dataset_name):
    print(f"🔍 Ищем датасет: {dataset_name}")
    url = f"{BASE_URL}/api/v1/dataset/"
    params = {
        "q": json.dumps(
            {
                "filters": [
                    {"col": "table_name", "opr": "eq", "value": dataset_name}
                ]
            }
        )
    }
    response = session.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка при поиске датасета: {response.text}")
    data = response.json()
    if data["count"] == 0:
        raise Exception(f"❌ Датасет '{dataset_name}' не найден")
    dataset_id = data["result"][0]["id"]
    print(f"✅ Найден датасет '{dataset_name}' с ID = {dataset_id}")
    return dataset_id


# ========================
# 3. Создать график
# ========================
def create_chart(dataset_id, chart_name, viz_type, form_data):
    print(f"📈 Создаём график: {chart_name} ({viz_type})")
    url = f"{BASE_URL}/api/v1/chart/"
    form_data["datasource"] = f"{dataset_id}__table"
    form_data["viz_type"] = viz_type
    form_data["row_limit"] = 1000

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
# 4. Основной процесс
# ========================
if __name__ == "__main__":
    try:
        login()

        # Получаем ID датасетов
        dataset_revenue = get_dataset_id_by_name("Выручка по странам")
        dataset_new_customers = get_dataset_id_by_name(
            "Новые клиенты по месяцам"
        )

        # 1. График: Выручка по странам (Bar Chart)
        print("\n📊 Создаём график: Выручка по странам")
        create_chart(
            dataset_id=dataset_revenue,
            chart_name="Выручка по странам",
            viz_type="dist_bar",
            form_data={
                "groupby": ["Страна"],
                "metrics": [
                    {
                        "label": "Выручка",
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "Выручка"},
                        "aggregate": "SUM",
                    }
                ],
                "y_axis_format": "SMART_NUMBER",
            },
        )

        time.sleep(2)

        # 2. График: Новые клиенты по месяцам (Time Series)
        print("\n📅 Создаём график: Новые клиенты по месяцам")
        create_chart(
            dataset_id=dataset_new_customers,
            chart_name="Новые клиенты по месяцам",
            viz_type="time_series",
            form_data={
                "x_axis": "Месяц",
                "metrics": [
                    {
                        "label": "Новые клиенты",
                        "expressionType": "SIMPLE",
                        "column": {"column_name": "Новые клиенты"},
                        "aggregate": "SUM",
                    }
                ],
                "y_axis_format": "SMART_NUMBER",
            },
        )

        print("\n🎉 Оба графика успешно созданы!")
        print(f"👉 Перейди в Superset: {BASE_URL}/chart/list/")
        print("   и найди графики:")
        print("   • 'Выручка по странам'")
        print("   • 'Новые клиенты по месяцам'")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
