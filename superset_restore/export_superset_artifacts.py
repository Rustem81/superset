# export_superset_artifacts.py
import requests
import json
import time
import yaml
import os
from typing import List

# ========================
# Конфигурация
# ========================
BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
OUTPUT_FILE = "superset_artifacts.yaml"

# Создаём сессию
session = requests.Session()


# ========================
# 1. Авторизация
# ========================
def login():
    print("🔐 Авторизуемся в Superset...")
    url = f"{BASE_URL}/api/v1/security/login"
    payload = {"username": USERNAME, "password": PASSWORD, "provider": "db"}
    try:
        response = session.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"❌ Ошибка авторизации: {response.text}")
        token = response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Авторизация прошла успешно")
    except Exception as e:
        raise Exception(f"❌ Не удалось авторизоваться: {e}")


# ========================
# 2. Получить все ID датасетов
# ========================
def get_all_dataset_ids() -> List[int]:
    print("🔍 Получаем все ID датасетов...")
    url = f"{BASE_URL}/api/v1/dataset/"
    params = {"q": json.dumps({"columns": ["id"]})}
    try:
        response = session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"❌ Ошибка получения датасетов: {response.text}")
        data = response.json()
        ids = [item["id"] for item in data["result"]]
        print(f"✅ Найдено {len(ids)} датасетов")
        return ids
    except Exception as e:
        print(f"⚠️ Ошибка при получении датасетов: {e}")
        return []


# ========================
# 3. Получить все ID графиков
# ========================
def get_all_chart_ids() -> List[int]:
    print("🔍 Получаем все ID графиков...")
    url = f"{BASE_URL}/api/v1/chart/"
    params = {"q": json.dumps({"columns": ["id"]})}
    try:
        response = session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"❌ Ошибка получения графиков: {response.text}")
        data = response.json()
        ids = [item["id"] for item in data["result"]]
        print(f"✅ Найдено {len(ids)} графиков")
        return ids
    except Exception as e:
        print(f"⚠️ Ошибка при получении графиков: {e}")
        return []


# ========================
# 4. Получить ID дашборда по названию
# ========================
def get_dashboard_id_by_title(title: str) -> int:
    print(f"🔍 Ищем дашборд по названию: {title}")
    url = f"{BASE_URL}/api/v1/dashboard/"
    params = {
        "q": json.dumps(
            {
                "filters": [
                    {"col": "dashboard_title", "opr": "eq", "value": title}
                ]
            }
        )
    }
    try:
        response = session.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"❌ Ошибка поиска дашборда: {response.text}")
        data = response.json()
        if data["count"] == 0:
            raise Exception(f"❌ Дашборд с названием '{title}' не найден")
        dashboard_id = data["result"][0]["id"]
        print(f"✅ Найден дашборд '{title}' с ID = {dashboard_id}")
        return dashboard_id
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit(1)


# ========================
# 5. Экспорт: Подключение к БД
# ========================
def export_database(database_id: int):
    print(f"🗄️ Экспортируем подключение к БД (ID={database_id})...")
    url = f"{BASE_URL}/api/v1/database/{database_id}/export/"
    try:
        response = session.get(url)
        if response.status_code != 200:
            raise Exception(f"❌ Ошибка экспорта БД: {response.text}")

        import zipfile
        from io import BytesIO

        zip_file = zipfile.ZipFile(BytesIO(response.content))
        for file_name in zip_file.namelist():
            if file_name.endswith(".yaml"):
                yaml_content = zip_file.read(file_name).decode("utf-8")
                return yaml.safe_load(yaml_content)
        raise Exception("❌ YAML с подключением к БД не найден")
    except Exception as e:
        print(f"⚠️ Не удалось экспортировать БД: {e}")
        return None


# ========================
# 6. Экспорт: Датасеты, Графики, Дашборд в YAML
# ========================
def export_to_yaml():
    print("📦 Экспортируем всё в YAML...")

    export_data = {
        "metadata": {
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "superset_url": BASE_URL,
            "export_tool": "export_superset_artifacts.py",
        },
        "database": None,
        "datasets": [],
        "charts": [],
        "dashboard": None,
    }

    # === 1. Экспорт БД (через ID из первого датасета) ===
    dataset_ids = get_all_dataset_ids()
    if dataset_ids:
        try:
            ds_url = f"{BASE_URL}/api/v1/dataset/{dataset_ids[0]}"
            ds_response = session.get(ds_url)
            if ds_response.status_code == 200:
                db_id = ds_response.json()["result"]["database"]["id"]
                export_data["database"] = export_database(db_id)
        except Exception as e:
            print(f"⚠️ Не удалось экспортировать БД: {e}")

    # === 2. Экспорт датасетов ===
    for ds_id in dataset_ids:
        url = f"{BASE_URL}/api/v1/dataset/{ds_id}"
        try:
            response = session.get(url)
            if response.status_code == 200:
                ds_data = response.json()["result"]
                export_data["datasets"].append(
                    {
                        "id": ds_data["id"],
                        "table_name": ds_data["table_name"],
                        "database_id": ds_data["database"]["id"],
                        "sql": ds_data.get("sql", "N/A"),
                    }
                )
        except Exception as e:
            print(f"⚠️ Ошибка при экспорте датасета {ds_id}: {e}")

    # === 3. Экспорт графиков ===
    chart_ids = get_all_chart_ids()
    for ch_id in chart_ids:
        url = f"{BASE_URL}/api/v1/chart/{ch_id}"
        try:
            response = session.get(url)
            if response.status_code == 200:
                ch_data = response.json()["result"]
                # ✅ Исправлено: безопасно получаем datasource
                datasource = ch_data.get("datasource")
                datasource_id = datasource["id"] if datasource else None
                datasource_type = datasource["type"] if datasource else None

                export_data["charts"].append(
                    {
                        "id": ch_data["id"],
                        "slice_name": ch_data["slice_name"],
                        "viz_type": ch_data["viz_type"],
                        "datasource_id": datasource_id,
                        "datasource_type": datasource_type,
                        "params": ch_data["params"],
                    }
                )
            else:
                print(
                    f"⚠️ Ошибка HTTP при получении графика {ch_id}: {response.status_code}"
                )
        except Exception as e:
            print(f"⚠️ Ошибка при экспорте графика {ch_id}: {e}")

    # === 4. Экспорт дашборда ===
    try:
        dashboard_id = get_dashboard_id_by_title(
            "Статистика лейбла"
        )  # ✅ Ты правильно изменил
        url = f"{BASE_URL}/api/v1/dashboard/{dashboard_id}"
        response = session.get(url)
        if response.status_code == 200:
            dash_data = response.json()["result"]
            export_data["dashboard"] = {
                "id": dash_data["id"],
                "dashboard_title": dash_data["dashboard_title"],
                "slug": dash_data["slug"],
                "position_json": json.loads(dash_data["position_json"])
                if isinstance(dash_data["position_json"], str)
                else dash_data["position_json"],
            }
        else:
            print(f"⚠️ Ошибка при получении дашборда: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Не удалось экспортировать дашборд: {e}")

    # === 5. Сохраняем в YAML ===
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(
            export_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
        )

    print(f"✅ Все артефакты экспортированы в: {OUTPUT_FILE}")


# ========================
# 7. Основной процесс
# ========================
if __name__ == "__main__":
    try:
        login()
        export_to_yaml()
        print(f"\n🎉 Экспорт завершён! Файл: {OUTPUT_FILE}")
        print("👉 Теперь запусти: python import_superset_artifacts.py")

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
