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
    print(f"📈 Создаём график: {chart_name}")
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
        raise Exception(
            f"❌ Ошибка создания графика '{chart_name}': {response.text}"
        )
    chart_id = response.json()["id"]
    print(f"✅ График '{chart_name}' создан (ID: {chart_id})")
    return chart_id


# ========================
# 4. Основной процесс
# ========================
if __name__ == "__main__":
    try:
        login()

        # Получаем ID датасета
        dataset_name = "Общая статистика"
        try:
            dataset_id = get_dataset_id_by_name(dataset_name)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print(
                "💡 Убедись, что датасет 'Общая статистика' существует в Superset"
            )
            exit(1)

        print(f"✅ Используем dataset_id = {dataset_id}")

        # Создаём 3 Big Number
        print("\n📊 Создаём Big Number графики...")

        # 1. Количество заказов
        create_chart(
            dataset_id=dataset_id,
            chart_name="Количество заказов",
            viz_type="big_number",
            form_data={
                "metric": {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "Количество заказов"},
                    "aggregate": "SUM",  # COUNT(*) уже посчитан, но Superset требует агрегацию
                },
                "y_axis_format": "SMART_NUMBER",
            },
        )

        # 2. Общая выручка
        create_chart(
            dataset_id=dataset_id,
            chart_name="Общая выручка",
            viz_type="big_number",
            form_data={
                "metric": {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "Общая выручка"},
                    "aggregate": "SUM",  # SUM(total) уже посчитан
                },
                "y_axis_format": "SMART_NUMBER",
            },
        )

        # 3. Средний чек
        create_chart(
            dataset_id=dataset_id,
            chart_name="Средний чек",
            viz_type="big_number",
            form_data={
                "metric": {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "Средний чек"},
                    "aggregate": "AVG",  # Здесь AVG — корректно, так как это среднее по заказам
                },
                "y_axis_format": "SMART_NUMBER",
            },
        )
        print("\n🎉 Все 3 Big Number графика успешно созданы!")
        print(
            f"👉 Перейди в Superset: {BASE_URL}/chart/list/?pageIndex=0&pageSize=25"
        )
        print(
            "   и найди графики с названиями: 'Количество заказов', 'Общая выручка', 'Средний чек'"
        )

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
