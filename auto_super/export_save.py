import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

session = requests.Session()


def login():
    url = f"{BASE_URL}/api/v1/security/login"
    payload = {"username": USERNAME, "password": PASSWORD, "provider": "db"}
    response = session.post(url, json=payload)
    token = response.json()["access_token"]
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )


def export_dashboards():
    """Экспорт всех дашбордов"""
    print("📤 Экспортируем дашборды...")
    response = session.get(f"{BASE_URL}/api/v1/dashboard/")
    dashboards = response.json().get("result", [])

    for db in dashboards:
        db_id = db["id"]
        db_detail = session.get(f"{BASE_URL}/api/v1/dashboard/{db_id}").json()

        filename = (
            f"dashboard_{db_id}_{db['dashboard_title'].replace(' ', '_')}.json"
        )
        with open(f"export/dashboards/{filename}", "w") as f:
            json.dump(db_detail, f, indent=2, ensure_ascii=False)
        print(f"💾 Сохранен дашборд: {db['dashboard_title']}")


def export_charts():
    """Экспорт всех графиков"""
    print("📊 Экспортируем графики...")
    response = session.get(f"{BASE_URL}/api/v1/chart/")
    charts = response.json().get("result", [])

    for chart in charts:
        chart_id = chart["id"]
        chart_detail = session.get(
            f"{BASE_URL}/api/v1/chart/{chart_id}"
        ).json()

        filename = (
            f"chart_{chart_id}_{chart['slice_name'].replace(' ', '_')}.json"
        )
        with open(f"export/charts/{filename}", "w") as f:
            json.dump(chart_detail, f, indent=2, ensure_ascii=False)
        print(f"💾 Сохранен график: {chart['slice_name']}")


def export_datasets():
    """Экспорт всех датасетов"""
    print("🗃️ Экспортируем датасеты...")
    response = session.get(f"{BASE_URL}/api/v1/dataset/")
    datasets = response.json().get("result", [])

    for ds in datasets:
        ds_id = ds["id"]
        ds_detail = session.get(f"{BASE_URL}/api/v1/dataset/{ds_id}").json()

        filename = f"dataset_{ds_id}_{ds['table_name'].replace(' ', '_')}.json"
        with open(f"export/datasets/{filename}", "w") as f:
            json.dump(ds_detail, f, indent=2, ensure_ascii=False)
        print(f"💾 Сохранен датасет: {ds['table_name']}")


def create_import_script():
    """Создание скрипта для импорта"""
    template = '''
import requests
import json
import os

BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

session = requests.Session()

def login():
    url = f"{BASE_URL}/api/v1/security/login"
    payload = {"username": USERNAME, "password": PASSWORD, "provider": "db"}
    response = session.post(url, json=payload)
    token = response.json()["access_token"]
    session.headers.update({{
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }})

def import_dashboards():
    """Импорт дашбордов"""
    print("📥 Импортируем дашборды...")
    for filename in os.listdir("export/dashboards"):
        if filename.endswith(".json"):
            with open(f"export/dashboards/{filename}", "r") as f:
                dashboard_data = json.load(f)
            
            # Создаем дашборд
            payload = {{
                "dashboard_title": dashboard_data["result"]["dashboard_title"],
                "slug": dashboard_data["result"]["slug"],
                "position_json": dashboard_data["result"]["position_json"],
                "published": True,
                "owners": [1]
            }}
            
            response = session.post(f"{BASE_URL}/api/v1/dashboard/", json=payload)
            if response.status_code == 201:
                print(f"✅ Импортирован дашборд: {{dashboard_data['result']['dashboard_title']}}")

def import_charts():
    """Импорт графиков"""
    print("📈 Импортируем графики...")
    for filename in os.listdir("export/charts"):
        if filename.endswith(".json"):
            with open(f"export/charts/{filename}", "r") as f:
                chart_data = json.load(f)
            
            payload = {{
                "slice_name": chart_data["result"]["slice_name"],
                "viz_type": chart_data["result"]["viz_type"],
                "datasource_type": chart_data["result"]["datasource_type"],
                "datasource_id": chart_data["result"]["datasource_id"],
                "params": chart_data["result"]["params"],
                "owners": [1]
            }}
            
            response = session.post(f"{BASE_URL}/api/v1/chart/", json=payload)
            if response.status_code == 201:
                print(f"✅ Импортирован график: {{chart_data['result']['slice_name']}}")

def import_datasets():
    """Импорт датасетов"""
    print("🗃️ Импортируем датасеты...")
    for filename in os.listdir("export/datasets"):
        if filename.endswith(".json"):
            with open(f"export/datasets/{filename}", "r") as f:
                dataset_data = json.load(f)
            
            payload = {{
                "database": dataset_data["result"]["database"]["id"],
                "schema": dataset_data["result"]["schema"],
                "table_name": dataset_data["result"]["table_name"],
                "owners": [1]
            }}
            
            response = session.post(f"{BASE_URL}/api/v1/dataset/", json=payload)
            if response.status_code == 201:
                print(f"✅ Импортирован датасет: {{dataset_data['result']['table_name']}}")

if __name__ == "__main__":
    login()
    import_datasets()
    import_charts()
    import_dashboards()
    print("🎯 Импорт завершен!")
'''

    with open("import_superset.py", "w") as f:
        f.write(template)
    print("📝 Создан скрипт для импорта: import_superset.py")


if __name__ == "__main__":
    # Создаем папки для экспорта
    os.makedirs("export/dashboards", exist_ok=True)
    os.makedirs("export/charts", exist_ok=True)
    os.makedirs("export/datasets", exist_ok=True)

    login()
    export_datasets()
    export_charts()
    export_dashboards()
    create_import_script()

    print("✅ Экспорт завершен! Файлы сохранены в папке export/")
