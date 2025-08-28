--🔹 Датасет 1: Sales Overview (Общая статистика)
SELECT
    COUNT(*) AS "Количество заказов",
    SUM(total) AS "Общая выручка",
    AVG(total) AS "Средний чек",
    MIN(invoice_date) AS "Первая продажа",
    MAX(invoice_date) AS "Последняя продажа"
FROM
    invoice;

--💡 Используется для Big Number и Text элементов 
-- 🔹 Датасет 2: Revenue by Country (Выручка по странам)
SELECT
    billing_country AS "Страна",
    COUNT(invoice_id) AS "Количество заказов",
    SUM(total) AS "Выручка",
    AVG(total) AS "Средний чек"
FROM
    invoice
GROUP BY
    billing_country
ORDER BY
    "Выручка" DESC;

-- 📊 Используется: Bar Chart, Pie Chart, Mapbox 
-- 🔹 Датасет 3: Top 10 Customers (Топ-10 клиентов)
SELECT
    c.first_name || ' ' || c.last_name AS "Имя клиента",
    c.country AS "Страна",
    c.email AS "Email",
    c.company AS "Компания",
    SUM(i.total) AS "Общая выручка",
    COUNT(i.invoice_id) AS "Количество заказов"
FROM
    customer c
    JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name,
    c.country,
    c.email,
    c.company
ORDER BY
    "Общая выручка" DESC LIMIT 10;

--📊 Используется: Table, Bar Chart
-- 🔹 Датасет 4: Customers by City (Клиенты по городам)
SELECT
    c.city AS "Город",
    c.country AS "Страна",
    COUNT(c.customer_id) AS "Количество клиентов",
    SUM(i.total) AS "Выручка"
FROM
    customer c
    JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY
    c.city,
    c.country
ORDER BY
    "Выручка" DESC;

--🌍 Используется: Mapbox, Bubble Chart 
--🔹 Датасет 5: Top 10 Artists (Топ-10 артистов)
SELECT
    ar.name AS "Артист",
    COUNT(il.track_id) AS "Количество продаж",
    SUM(il.unit_price) AS "Выручка"
FROM
    artist ar
    JOIN album al ON ar.artist_id = al.artist_id
    JOIN track t ON al.album_id = t.album_id
    JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY
    ar.artist_id,
    ar.name
ORDER BY
    "Выручка" DESC LIMIT 10;

--🎵 Используется: Bar Chart, Table
--🔹 Датасет 6: Monthly Revenue (Выручка по месяцам)
/*
SELECT 
DATE_TRUNC('month', invoice_date)::date AS "Месяц",
SUM(total) AS "Выручка"
FROM invoice
GROUP BY "Месяц"
ORDER BY "Месяц";*/
--📈 Используется: Time Series, Line Chart
--🔹 Датасет 7: Top 10 Genres (Топ-10 жанров)
SELECT
    g.name AS "Жанр",
    COUNT(il.track_id) AS "Количество продаж",
    SUM(il.unit_price) AS "Выручка"
FROM
    genre g
    JOIN track t ON g.genre_id = t.genre_id
    JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY
    g.genre_id,
    g.name
ORDER BY
    "Выручка" DESC LIMIT 10;

--📊 Используется: Pie Chart, Bar Chart
-- 🔹 Датасет 8: Top 10 Tracks (Топ-10 треков)
SELECT
    t.name AS "Название трека",
    ar.name AS "Артист",
    g.name AS "Жанр",
    ROUND(t.milliseconds / 60000.0, 2) AS "Длительность (мин)",
    il.unit_price AS "Цена",
    COUNT(il.track_id) AS "Количество продаж"
FROM
    track t
    JOIN invoice_line il ON t.track_id = il.track_id
    JOIN album al ON t.album_id = al.album_id
    JOIN artist ar ON al.artist_id = ar.artist_id
    JOIN genre g ON t.genre_id = g.genre_id
GROUP BY
    t.track_id,
    t.name,
    ar.name,
    g.name,
    t.milliseconds,
    il.unit_price
ORDER BY
    "Количество продаж" DESC LIMIT 10;

--🎧 Используется: Table, Bar Chart
-- 🔹 Датасет 9: Media Type Performance (Выручка по типам носителей)
SELECT
    mt.name AS "Тип носителя",
    COUNT(il.track_id) AS "Количество продаж",
    SUM(il.unit_price) AS "Выручка"
FROM
    media_type mt
    JOIN track t ON mt.media_type_id = t.media_type_id
    JOIN invoice_line il ON t.track_id = il.track_id
GROUP BY
    mt.media_type_id,
    mt.name
ORDER BY
    "Выручка" DESC;

-- 📼 Используется: Pie Chart, Table
-- 🔹 Датасет 10: Support Rep Performance (Эффективность менеджеров)
SELECT
    e.first_name || ' ' || e.last_name AS "Менеджер",
    e.email AS "Email",
    COUNT(c.customer_id) AS "Количество клиентов",
    SUM(i.total) AS "Выручка от клиентов"
FROM
    employee e
    JOIN customer c ON e.employee_id = c.support_rep_id
    JOIN invoice i ON c.customer_id = i.customer_id
GROUP BY
    e.employee_id,
    e.first_name,
    e.last_name,
    e.email
ORDER BY
    "Выручка от клиентов" DESC;

--👔 Используется: Bar Chart, Table
-- 🔹 Датасет 11: New Customers by Month (Новые клиенты по месяцам)
/*
SELECT 
DATE_TRUNC('month', i.invoice_date)::date AS "Месяц",
COUNT(DISTINCT c.customer_id) AS "Новые клиенты"
FROM customer c
JOIN invoice i ON c.customer_id = i.customer_id
WHERE i.invoice_date = (
SELECT MIN(invoice_date)
FROM invoice i2
WHERE i2.customer_id = c.customer_id
)
GROUP BY "Месяц"
ORDER BY "Месяц";
 */
-- 📈 Используется: Time Series, Line Chart

