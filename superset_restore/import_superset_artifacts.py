# import_superset_artifacts.py
import requests
import yaml
import os
import time
import io
import zipfile
from typing import Dict, Any

# ========================
# Конфигурация
# ========================
BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
YAML_FILE = "superset_artifacts.yaml"

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
    print("✅ Авторизация прошла успешно")


# ========================
# 2. Создать ZIP в памяти из словаря
# ========================
def create_zip_from_dict(data: Dict[str, Any], filename: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            filename,
            yaml.dump(data, allow_unicode=True, sort_keys=False, indent=2),
        )
    buffer.seek(0)
    return buffer.read()


# ========================
# 3. Импорт подключения к БД
# ========================
def import_database(database_data):
    print("🗄️ Импортируем подключение к БД...")
    url = f"{BASE_URL}/api/v1/database/import/"

    # Структура, которую ожидает Superset
    zip_data = {
        "version": "1.0.0",
        "type": "Database",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "databases": {
            "__root__": database_data  # 🔥 Ключ должен быть __root__
        },
    }

    # Создаём ZIP в памяти
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "metadata.yaml",
            yaml.dump(
                {
                    "version": "1.0.0",
                    "type": "Database",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                allow_unicode=True,
            ),
        )
        zf.writestr(
            "databases/__root__.yaml",
            yaml.dump(database_data, allow_unicode=True),
        )

    buffer.seek(0)

    # Отправляем
    files = {
        "file": ("database.zip", buffer.read(), "application/zip"),
        "overwrite": (None, "true"),
    }
    response = session.post(url, files=files)
    if response.status_code == 201:
        print("✅ Подключение к БД импортировано")
        return True
    else:
        print(
            f"❌ Ошибка импорта БД: {response.status_code} — {response.text}"
        )
        return False


# ========================
# 4. Импорт датасетов
# ========================
def import_datasets(dataset_list: list):
    print(f"📊 Импортируем {len(dataset_list)} датасетов...")
    url = f"{BASE_URL}/api/v1/dataset/import/"

    for ds in dataset_list:
        print(f"  ➤ Импорт: {ds['table_name']} (ID={ds['id']})")

        zip_data = {
            "datasets": [ds],
            "version": "1.0.0",
            "type": "Dataset",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        zip_content = create_zip_from_dict(zip_data, "dataset_metadata.yaml")

        files = {
            "file": ("dataset.zip", zip_content, "application/zip"),
            "overwrite": (None, "true"),
        }
        response = session.post(url, files=files)
        if response.status_code == 201:
            print(f"    ✅ Датасет '{ds['table_name']}' импортирован")
        else:
            print(
                f"    ❌ Ошибка: {response.status_code} — {response.text[:300]}"
            )
        time.sleep(0.5)

    print("✅ Все датасеты обработаны")


# ========================
# 5. Импорт графиков
# ========================
def import_charts(chart_list: list):
    print(f"📈 Импортируем {len(chart_list)} графиков...")
    url = f"{BASE_URL}/api/v1/chart/import/"

    for ch in chart_list:
        print(f"  ➤ Импорт: {ch['slice_name']} (ID={ch['id']})")

        zip_data = {
            "charts": {str(ch["id"]): ch},
            "version": "1.0.0",
            "type": "Chart",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        zip_content = create_zip_from_dict(zip_data, "chart_metadata.yaml")

        files = {
            "file": ("chart.zip", zip_content, "application/zip"),
            "overwrite": (None, "true"),
        }
        response = session.post(url, files=files)
        if response.status_code == 201:
            print(f"    ✅ График '{ch['slice_name']}' импортирован")
        else:
            print(
                f"    ❌ Ошибка: {response.status_code} — {response.text[:300]}"
            )
        time.sleep(0.5)

    print("✅ Все графики обработаны")


# ========================
# 6. Импорт дашборда
# ========================
def import_dashboard(dashboard_data: Dict):
    print("🎨 Импортируем дашборд...")
    url = f"{BASE_URL}/api/v1/dashboard/import/"

    zip_data = {
        "dashboards": {str(dashboard_data["id"]): dashboard_data},
        "version": "1.0.0",
        "type": "Dashboard",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    zip_content = create_zip_from_dict(zip_data, "dashboard_metadata.yaml")

    files = {
        "file": ("dashboard.zip", zip_content, "application/zip"),
        "overwrite": (None, "true"),
    }
    response = session.post(url, files=files)
    if response.status_code == 201:
        print("✅ Дашборд импортирован")
        return True
    else:
        print(
            f"❌ Ошибка импорта дашборда: {response.status_code} — {response.text[:500]}"
        )
        return False


# ========================
# 7. Основной процесс
# ========================
if __name__ == "__main__":
    try:
        login()

        if not os.path.exists(YAML_FILE):
            raise Exception(
                f"❌ Файл {YAML_FILE} не найден. Убедитесь, что он в той же папке."
            )

        with open(YAML_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        print(
            f"📦 Найдено в YAML: "
            f"БД: {'да' if data.get('database') else 'нет'}, "
            f"Датасеты: {len(data.get('datasets', []))}, "
            f"Графики: {len(data.get('charts', []))}, "
            f"Дашборд: {'да' if data.get('dashboard') else 'нет'}"
        )

        # === 1. Импорт БД ===
        if "database" in data:
            import_database(data["database"])
        else:
            print(
                "⚠️ Подключение к БД не найдено в YAML. Убедитесь, что оно создано вручную."
            )

        # === 2. Импорт датасетов ===
        if "datasets" in data:
            import_datasets(data["datasets"])

        # === 3. Импорт графиков ===
        if "charts" in data:
            import_charts(data["charts"])

        # === 4. Импорт дашборда ===
        if "dashboard" in data:
            import_dashboard(data["dashboard"])

        print(f"\n🎉 Восстановление завершено!")
        print(
            f"👉 Открой дашборд: {BASE_URL}/superset/dashboard/{data['dashboard']['id']}/?standalone=true"
        )

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
