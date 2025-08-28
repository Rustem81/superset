# 🚀 Финальный проект: Анализ данных в Apache Superset

> **Цель проекта**: Создать функциональный, красивый и безопасный дашборд на основе реальной реляционной базы данных, демонстрирующий навыки работы с инфраструктурой, SQL, визуализацией и кастомизацией.

---

## 🌐 Этап 1: Выбор открытой реляционной базы данных

### 🔹 Рекомендуемая БД: [Chinook](https://github.com/lerocha/chinook-database)
- **Описание**: Модель музыкального магазина (клиенты, треки, альбомы, продажи).
- **Почему?**
  - Реалистичная структура с JOIN’ами.
  - Подходит для аналитики: выручка, гео, поведение клиентов.
  - Есть `.sql` дамп для PostgreSQL.
- **Ссылка**:  
  [Chinook_PSQL.sql](https://github.com/lerocha/chinook-database/blob/master/ChinookDatabase/DataSources/Chinook_PSQL.sql)

---

## 🖥️ Этап 2: Развертывание стенда (PostgreSQL + Superset)

### 🛠 Способ: `docker-compose.yml`

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chinook
      POSTGRES_USER: superset
      POSTGRES_PASSWORD: superset
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./Chinook_PSQL.sql:/docker-entrypoint-initdb.d/Chinook_PSQL.sql

  superset:
    image: apache/superset:latest
    depends_on:
      - postgres
    ports:
      - "8088:8088"
    environment:
      SUPERSET_SECRET_KEY: your_very_secret_key_here
      DATABASE_URL: postgresql://superset:superset@postgres:5432/chinook
    volumes:
      - ./superset_config.py:/home/superset/superset_config.py
    command: >
      bash -c "
        pip install psycopg2-binary &&
        superset db upgrade &&
        superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin &&
        superset init &&
        superset run -p 8088"