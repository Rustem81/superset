import requests
import json
import time

# Конфигурация
BASE_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# Создаём сессию
session = requests.Session()


def login():
    """Авторизация в Superset"""
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


def get_all_dashboards():
    """Получить все дашборды"""
    print("📋 Получаем список всех дашбордов...")
    url = f"{BASE_URL}/api/v1/dashboard/"
    response = session.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка при получении дашбордов: {response.text}")

    dashboards = response.json().get("result", [])
    print(f"✅ Найдено дашбордов: {len(dashboards)}")
    return dashboards


def get_all_charts():
    """Получить все графики"""
    print("📊 Получаем список всех графиков...")
    url = f"{BASE_URL}/api/v1/chart/"
    response = session.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка при получении графиков: {response.text}")

    charts = response.json().get("result", [])
    print(f"✅ Найдено графиков: {len(charts)}")
    return charts


def get_all_datasets():
    """Получить все датасеты (включая виртуальные)"""
    print("🗃️ Получаем список всех датасетов...")
    url = f"{BASE_URL}/api/v1/dataset/"
    response = session.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка при получении датасетов: {response.text}")

    datasets = response.json().get("result", [])
    print(f"✅ Найдено датасетов: {len(datasets)}")
    return datasets


def get_all_virtual_datasets():
    """Получить только виртуальные датасеты"""
    print("🔍 Получаем список виртуальных датасетов...")
    url = f"{BASE_URL}/api/v1/dataset/"
    response = session.get(url)
    if response.status_code != 200:
        raise Exception(f"❌ Ошибка при получении датасетов: {response.text}")

    all_datasets = response.json().get("result", [])
    virtual_datasets = [
        ds for ds in all_datasets if ds.get("kind") == "virtual"
    ]
    print(f"✅ Найдено виртуальных датасетов: {len(virtual_datasets)}")
    return virtual_datasets


def delete_dashboard(dashboard_id, dashboard_name):
    """Удалить дашборд"""
    url = f"{BASE_URL}/api/v1/dashboard/{dashboard_id}"
    response = session.delete(url)
    if response.status_code == 200:
        print(f"🗑️ Удалён дашборд: {dashboard_name} (ID: {dashboard_id})")
        return True
    else:
        print(
            f"⚠️ Не удалось удалить дашборд {dashboard_name}: {response.text}"
        )
        return False


def delete_chart(chart_id, chart_name):
    """Удалить график"""
    url = f"{BASE_URL}/api/v1/chart/{chart_id}"
    response = session.delete(url)
    if response.status_code == 200:
        print(f"🗑️ Удалён график: {chart_name} (ID: {chart_id})")
        return True
    else:
        print(f"⚠️ Не удалось удалить график {chart_name}: {response.text}")
        return False


def delete_dataset(dataset_id, dataset_name, is_virtual=False):
    """Удалить датасет"""
    url = f"{BASE_URL}/api/v1/dataset/{dataset_id}"
    response = session.delete(url)
    if response.status_code == 200:
        type_str = "виртуальный датасет" if is_virtual else "датасет"
        print(f"🗑️ Удалён {type_str}: {dataset_name} (ID: {dataset_id})")
        return True
    else:
        print(f"⚠️ Не удалось удалить датасет {dataset_name}: {response.text}")
        return False


def cleanup_superset():
    """Основная функция очистки"""
    try:
        # Авторизация
        login()

        # Удаляем дашборды
        dashboards = get_all_dashboards()
        dashboard_count = 0
        for dashboard in dashboards:
            if dashboard.get("id") and dashboard.get("dashboard_title"):
                if delete_dashboard(
                    dashboard["id"], dashboard["dashboard_title"]
                ):
                    dashboard_count += 1
                time.sleep(0.1)

        # Удаляем графики
        charts = get_all_charts()
        chart_count = 0
        for chart in charts:
            if chart.get("id") and chart.get("slice_name"):
                if delete_chart(chart["id"], chart["slice_name"]):
                    chart_count += 1
                time.sleep(0.1)

        # Удаляем ВСЕ датасеты (обычные и виртуальные)
        datasets = get_all_datasets()
        dataset_count = 0
        virtual_count = 0

        for dataset in datasets:
            if dataset.get("id") and dataset.get("table_name"):
                is_virtual = dataset.get("kind") == "virtual"
                if delete_dataset(
                    dataset["id"], dataset["table_name"], is_virtual
                ):
                    dataset_count += 1
                    if is_virtual:
                        virtual_count += 1
                time.sleep(0.1)

        print("\n" + "=" * 50)
        print("🎯 Очистка завершена!")
        print(f"🗑️ Удалено дашбордов: {dashboard_count}")
        print(f"🗑️ Удалено графиков: {chart_count}")
        print(
            f"🗑️ Удалено датасетов: {dataset_count} (из них виртуальных: {virtual_count})"
        )
        print("=" * 50)

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


def confirm_deletion():
    """Подтверждение удаления"""
    print("⚠️  ВНИМАНИЕ: Этот скрипт удалит ВСЕ объекты в Superset!")
    print("⚠️  Будут удалены:")
    print("     - Все дашборды")
    print("     - Все графики (charts)")
    print("     - Все датасеты (обычные и виртуальные)")
    print("⚠️  Это действие нельзя отменить!")

    confirmation = input("Введите 'DELETE_ALL' для подтверждения: ")
    if confirmation == "DELETE_ALL":
        return True
    else:
        print("❌ Отменено пользователем")
        return False


# Запуск
if __name__ == "__main__":
    print("🧹 Superset Cleanup Tool")
    print("=" * 40)
    print("Удаляет ВСЕ дашборды, графики и датасеты")
    print("=" * 40)

    if confirm_deletion():
        cleanup_superset()
    else:
        print("Операция отменена")
