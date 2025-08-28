https://github.com/lerocha/chinook-database?spm=a2ty_o01.29997173.0.0.d9b6c921mCqbek

wget https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_PostgreSql.sql -O Chinook_PostgreSql.sql



psql -h 192.168.1.69 -p 5432 -U admin



postgresql://admin:admin@postgres:5432/chinook_serial