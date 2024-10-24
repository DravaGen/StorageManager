
# Deploy

1. Настраиваем переменные окружения:

  * `BASE_DIRECTORY` - полный путь до папки, где будут храниться все файлы

  * `PSQL_USER` - имя пользователя postgres
  * `PSQL_PASSWORD` - пароль от postgres
  * `PSQL_DATABASE` - название базы данных в postgres
  * `PSQL_HOST` - хост postgres, по умолчанию localhost
  * `PSQL_PORT` - порт postgres, по умолчанию 5432
  * `REDIS_HOST` - хост redis, по умолчанию localhost
  * `REDIS_PORT` - порт redis, по умолчанию 6379

  * `DEBUG` - переключатель режима разработки, True/False

2. Для поднятия базы данных убедитесь, что DEBUG = True, и запустить raise_database.py
3. Для локального запуска достаточно uvicorn app:app


## Аутентификация

Для входа в систему используйте следующий эндпоинт:

### POST /auth/login

**Важно:** В документации FastAPI (по адресу `/docs`) параметр для входа называется `username`, но на самом деле это поле ожидает ваш `email`. Пожалуйста, используйте его при выполнении запроса.
