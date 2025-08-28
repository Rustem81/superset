import requests


def check_superset_api():
    BASE_URL = "http://localhost:8088"

    print("🔍 Проверяем доступность Superset API...")

    # Проверяем основные endpoints
    endpoints = [
        "/api/v1/security/login",
        "/swagger/v1/swagger.json",
        "/api/v1/database/",
        "/health",
    ]

    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Ошибка: {e}")


if __name__ == "__main__":
    check_superset_api()
